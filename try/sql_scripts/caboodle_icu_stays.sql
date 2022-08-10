/***************************** ICU Stays Registry Base Query ***************************************
Basic ICU stats + COVID status for Adult ICUs

-- Issues
There are still a number of outstanding issues that need fixing before this can be a truly reliable
source of information
1. There are sometimes very short-lived stays on the ICU, sometimes with a minute or so's gap before
the patient is readmitted to the same ICU. These need to be dealt with as the patient clearly isn't
being discharged and readmitted. There's a commented out query at the bottom of the script to help 
identify these encounters.

2. Some IcuStayEndInstants are NULL when they clearly shouldn't be. Same for CrossIcuStayEndInstant.

3. I need to rewrite the query which generates IDs for the CrossICUStay and ICNARC blocks so that
instead of being an unstable number it picks up the first IcuStayBlockID.

4. It would be good to find and pull in the field that lists the hospital where the patient was
transferred from


-- Things this does handle
Issues with the ICU Stay Registry that this addresses
1. Creates unique IDs for CrossICuStays and also ICNARC-equivalent (eg: Site-based) ICU Stay Blocks
2. Filters out visits to the PLEX room on MITU and also SR-11 on MITU if the visit is short
3. Filters out Test patients
4. Creates a flag for patients who have a suspciously long LOS and a missing CrossICU/ICU Stay End Instant.

More detail is given in the comments related to the #icu table.

****************************************************************************************************/


/************************************* COVID Status ************************************************

We bring in two sources of truth.
The first is the infection control status (#ic_covid)
Sometimes infection control add multiple COVID Status entries to the patient record.
These either seem to be extensions of the original infectious period or updates.
Occasionally there seem to be errors where the COVID status is reactivated.
We deal with all this by setting the COVID onset /resolved to min and max values respectively
From manually inspecting a sample of the data this seems to be a sensible assumption.


****************************************************************************************************/
DROP TABLE IF EXISTS #ic_covid;
SELECT [PAT_ENC_CSN_ID]                                         EncounterEpicCsn
      , [PAT_MRN_ID]                                            PrimaryMrn
      , [INFECTION_STATUS]                                      CovidStatus
      , min([INFECTION_STATUS_ONSET_DTTM])                      CovidOnsetInstant
      , max([INFECTION_RESOLVE_DTTM])                           CovidResolvedInstant
      , case when max([INFECTION_RESOLVE_DTTM]) is null
             then GETDATE()
             else max([INFECTION_RESOLVE_DTTM]) end             CovidResolvedBounded
      , min([INFECTIOUS_START_DATE])                            InfectiousStartInstant
      , max([INFECTIOUS_END_DATE])                              InfectiousEndInstat
  INTO #ic_covid
  FROM [CABOODLE_REPORT].[WIP].[COVDM_INF_STATUS]
  WHERE INFECTION_STATUS = 'COVID confirmed'
  GROUP BY PAT_ENC_CSN_ID, PAT_MRN_ID, INFECTION_STATUS

/************************************* Ward Moves ************************************************

Sadly the ICU Stay Registry doesn't always find the previous department so we've manually computed
the patient journey to allow us to work out where thw prior location was


****************************************************************************************************/
DROP TABLE if exists #WardMoves ;

-- Start by selecting encounters where the patient went to ICU at some point
-- Filter out those weird 2018 admissions. We have to use both start and end
-- date keys to account for people who were admitted to ICU prior to Epic Go Live
-- but were still present on the unit and people who are currently on the ICU and so
-- don't have an end date yet.
WITH IcuEncounters as (
    SELECT  distinct plef.EncounterKey
      FROM  PatientLocationEventFact plef
      JOIN  DepartmentDim dd
        ON  plef.DepartmentKey = dd.DepartmentKey
     WHERE  dd.DepartmentType = 'ICU'
            AND plef.EndDateKey > 20190401 OR plef.StartDateKey > 20190401
),

-- Standard Gaps and Islands query to group all contiguous events on the same unit
PlefSeq as (
    SELECT  icu.EncounterKey
            , plef.PatientLocationEventKey
            , plef.PatientKey
            , plef.DepartmentKey
            , dd.DepartmentName
            , dd.DepartmentType
            , dd.DepartmentSpecialty
            , CASE  WHEN DepartmentSpecialty in ('Anaesthetics', 'Diagnostic Imaging - Radiology', 'Gastroenterology - Endoscopy', 'Rapid Response')
                            OR DepartmentName = '*Not Applicable'
                            OR DepartmentType = '*Unknown'
                    THEN 0 ELSE 1
                    END as IsCensusLocation
            , plef.CensusLocationKey
            , plef.LocationKey
            , plef.StartInstant
            , plef.EndInstant
            , ROW_NUMBER() OVER(order by concat(plef.EncounterKey,convert(varchar,plef.StartInstant,23))) -
            ROW_NUMBER() over(partition by plef.DepartmentKey order by concat(plef.EncounterKey,convert(varchar,plef.StartInstant,23))) as grouper
     FROM   IcuEncounters icu
LEFT JOIN   PatientLocationEventFact plef
       ON   icu.EncounterKey = plef.EncounterKey
LEFT JOIN   DepartmentDim dd
        ON  plef.DepartmentKey = dd.DepartmentKey
),

-- This finishes off the gaps and islands algorithm but filters out non-census locations so they don;t break up
-- ICU admissions. It then joins to the ICU Stays Registry table to get the corresponding ICUStayBlockID
DeptSeq as (
        SELECT  ps.EncounterKey
                , ps.PatientKey
                , ps.DepartmentKey
                , ps.DepartmentName
                , ps.DepartmentType
                , ps.DepartmentSpecialty
                , max(ps.IsCensusLocation)      as IsCensusLocation
                , max(icu.IcuStayBlockId)   as IcuStayBlockId
                , min(ps.StartInstant)      as StartInstant
                , max(ps.EndInstant)        as EndInstant
         FROM   PlefSeq ps
    LEFT JOIN   IcuStayRegistryDataMart icu
           ON   ps.EncounterKey = icu.EncounterKey AND ps.StartInstant = icu.IcuStayStartInstant
        WHERE   IsCensusLocation = 1
     GROUP BY   grouper
                , ps.DepartmentKey
                , ps.EncounterKey
                , ps.PatientKey
                , DepartmentName
                , DepartmentType
                , DepartmentSpecialty
)

-- Get previous and next department IDs which are needed to repair the flaws in the ICU Stays registry
SELECT  EncounterKey
        , PatientKey
        , DepartmentKey
        , DepartmentName
        , DepartmentType
        , DepartmentSpecialty
        , IsCensusLocation
        , IcuStayBlockId
        , StartInstant
        , EndInstant
        , DATEDIFF(MINUTE, StartInstant, EndInstant) as WardLosMins
        , LAG(DepartmentKey) OVER (PARTITION BY EncounterKey ORDER BY StartInstant) as PrevDepartmentKey
        , LAG(DepartmentName) OVER (PARTITION BY EncounterKey ORDER BY StartInstant) as PrevDepartmentName
        , LEAD(DepartmentKey) OVER (PARTITION BY EncounterKey ORDER BY StartInstant) as NextDepartmentKey
        , LEAD(DepartmentName) OVER (PARTITION BY EncounterKey ORDER BY StartInstant) as NextDepartmentName
  INTO  #WardMoves
  FROM  DeptSeq
  --WHERE DATEDIFF(MINUTE, StartInstant, EndInstant) > 5


/**************************************** #icu *****************************************************
This table provides the basic skeleton for the query, pulling in patient demographics and encounter
details. Although the column ordering suggests that this is a patient level query the unit of analysis
is a stay on an individual ICU but with helpers that allow aggregration at site or trust level

To help with temporal joins for patients still on the ICU is it necessary to creat versions of end times 
which replace NULL end dates with the current date/time. These columns are the Bounded columns.

The ICNARC Block ID looks like some pretty gnarly SQL but is actually doing something very simple.
It takes the Cross ICU Stay Block ID, which we we generate as part of this query, and concatenates that
with a hyphen and a grouper generated by the classic Gaps and Islands SQL. We need to concatenate the 
grouper to the CrossICUBlockID because the grouper is otherwise not unique.

We exclude EGA ICUs but the query should automatically pull in other non-EGA ICUs as they appear

-- Department Keys
6387    EGA E02 SCBU
6382    EGA E02 NRVY
6385    EGA E02 NICU

32934   T07 CV
35375   UCH T06 PACU
30369   UCH P03 CV
6338    UCH T03 ICU

30217   GWB L01W

9564    WMS CCU

8050    NHNN MITU
8057    NHNN SITU
38628   NHNN C1 NCCU 1st floor
38663   NHNN c0 NCCU Ground floor

-- Transfers
There are a number of different ways a transferred patient might be identified
- Admission Source = Other NHS Hospital
- Admission Type = Emergency Admission - Transfer of Admitted Patient from another Hospital Provider
- The prior department is NULL
- The Encounter Start and ICU Stay Start are identical

SQL for these conditions is below

AdmissionSource = 'Other NHS Hospital - Ward for General Patients, Younger Physically Disabled, or A&E'
OR AdmissionType = 'Emergency Admission - Transfer of Admitted Patient from another Hospital Provider'
OR AdmittedFrom is null
OR DATEDIFF(MINUTE, EncounterStartInstant, CrossIcuStayStartInstant) = 0

Use of any of the criteria (ie: max sensitivity, min specificity) yields 206 CrossIcuStays
between '2021-04-01' and '2021-11-01'

Stats for the individual rules are listed below
AdmissionType = transfer: 122
AdmittedFrom = null: 135
no difference between encounter and icu stay start time: 125

There is frequent logical disparity between Admission Method and Admission Source indicating that these
field are unreliable either alone or in combination.

Prior department is sometimes NULL for patients admitted from ED. Further investigation needed

The no difference between encounter and Cross ICU Stay Start seems pretty reliable.
Manual inspection of a handful where peior ward is NULL but there is a time difference between
Cross ICU Stay Start shows that when there is a gap of time there has usually been an error in 
recording the prior location.


****************************************************************************************************/
DROP TABLE IF EXISTS #icu;
SELECT 
      
      -- Patient Demographics
      ef.PatientKey
      ,pd.[PatientEpicId]
      ,pd.PrimaryMrn
      ,pd.NhsNumber
      ,FirstName
      ,LastName
      ,BirthDate
      ,floor([AgeAtIcuStayStart])                                   AgeAtIcuStayStart
      ,Sex
      ,case when Ethnicity = '*Unspecified'
            then NULL
            else Ethnicity end                                      Ethnicity

      -- ICU Stay Details
      ,DENSE_RANK() over 
        (order by CrossIcuStayStartInstant, icu.EncounterKey)       CrossIcuStayBlockId
      ,CrossIcuStayStartInstant
      ,CrossIcuStayEndInstant
      ,case when CrossIcuStayEndInstant is null
            then getdate()
            else CrossIcuStayEndInstant
            end                                                     CrossIcuStayEndBounded 
      ,datediff(minute,
            CrossIcuStayStartInstant, 
            CrossIcuStayEndInstant)                                 CrossIcuLOSMinutes
     
      , case when CrossIcuStayEndInstant is NULL then 'Ongoing'
             when DeathDate is NULL then 'Alive'
             when DeathDate > CrossIcuStayEndInstant then 'Alive at ICU d/c but died later'
             else 'Died' end                                        StatusAtCrossIcuStayEnd
      , case when CrossIcuStayEndInstant is NULL 
               and datediff(day, CrossIcuStayStartInstant, getdate()) > 365
               then 1 end                                           SuspiciouslyLongCrossIcuStay
      , concat(
                cast (DENSE_RANK() over 
                        (order by CrossIcuStayStartInstant
                                  , icu.EncounterKey) 
                      as varchar
                     )
                , '-'
                , cast(DENSE_RANK() over
                        (partition by CrossIcuStayStartInstant
                                     , icu.EncounterKey
                          order by IcuStayStartInstant) 
                      -
                    DENSE_RANK() over
                        (partition by CrossIcuStayStartInstant
                                      , icu.EncounterKey
                                      , dd.LocationAbbreviation
                         order by IcuStayStartInstant)
                    as varchar)     
                )                                                   IcnarcCovidBlockId

                
      ,icu.IcuStayBlockId
      ,dd.LocationAbbreviation                                      as [Site]
      ,plef.CensusLocationKey                                       as FirstBedCensusLocKey
      ,dd4.BedName                                                  as FirstBedAdmittedTo
      ,case when dd.LocationAbbreviation = 'GWB' then 1 else 0 end  as TreatedAtGWB
      ,case when dd.LocationAbbreviation = 'QSC' then 1 else 0 end  as TreatedAtQS
      ,case when dd.LocationAbbreviation = 'WMS' then 1 else 0 end  as TreatedAtWMS
      ,case when dd.LocationAbbreviation = 'UCHC' then 1 else 0 end as TreatedAtUCH
      ,case when dd.DepartmentKey = 35375 then 1 else 0 end         as TreatedOnT06
      ,dd.DepartmentName                                            Icu
      ,icu.DepartmentKey
      ,wm.PrevDepartmentName
      ,case when dd2.DepartmentName = '*Unspecified'
            then NULL
            else dd2.DepartmentName end                             AdmittedFrom
      ,dd2.DepartmentType                                           AdmittedFromDeptType

      -- ICU LOS Details
      ,IcuStayStartInstant
      ,[IcuStayEndInstant]
      ,case when IcuStayEndInstant is null
            then getdate()
            else IcuStayEndInstant
            end                                                     IcuStayEndBounded 
      ,IcuLengthOfStay

      -- ICU Discharge Details
      ,wm.NextDepartmentName
      ,case when dd3.DepartmentName = '*Unspecified'
            then NULL
            else dd3.DepartmentName end                             DischargedTo
      , case when IcuStayEndInstant is NULL then 'Ongoing'
             when DeathDate is NULL then 'Alive'
             when DeathDate > IcuStayEndInstant then 'Alive at ICU d/c but died later'
             else 'Died' end                                        StatusAtIcuStayEnd
      , case when IcuStayEndInstant is NULL 
                  and datediff(day, IcuStayStartInstant, getdate()) > 365
                  then 1  end                                       SuspiciouslyLongIcuStay


      -- Encounter Details
      , icu.[EncounterKey]
      , ef.EncounterEpicCsn
      , case when haf.AdmissionSource = '*Unspecified'
            then NULL
            else haf.AdmissionSource end                            AdmissionSource
      , haf.AdmissionType
      , ef.[Date]                                                   EncounterStartInstant
      , ef.EndInstant                                               EncounterEndInstant
      , case when haf.DischargeDestination_X = '*Unspecified'
            then NULL
            else haf.DischargeDestination_X end                     DischargeDestination
      , case when haf.DischargeDisposition = '*Unspecified'
            then NULL
            else haf.DischargeDisposition end                       DischargeDisposition  
      , DeathInstant

      -- COVID Status
      , ic.CovidStatus
      , ic.CovidOnsetInstant
      , ic.CovidResolvedInstant

  INTO #icu
  FROM [CABOODLE_REPORT].[dbo].[IcuStayRegistryDataMart]            icu
  join [CABOODLE_REPORT].[dbo].PatientLocationEventFact             plef
    on icu.EncounterKey = plef.EncounterKey
       and icu.IcuStayStartInstant = plef.StartInstant
  join [CABOODLE_REPORT].[dbo].DepartmentDim                        dd
    on icu.DepartmentKey = dd.DepartmentKey
  join [CABOODLE_REPORT].[dbo].DepartmentDim                        dd2
    on icu.PreviousDepartmentKey = dd2.DepartmentKey
  join [CABOODLE_REPORT].[dbo].DepartmentDim                        dd3
    on icu.PreviousDepartmentKey = dd3.DepartmentKey
  join DepartmentDim                                                dd4
    on plef.CensusLocationKey = dd4.DepartmentKey
  join [CABOODLE_REPORT].[dbo].EncounterFact                        ef
    on icu.EncounterKey = ef.EncounterKey
  join [CABOODLE_REPORT].[dbo].PatientDim                           pd
    on ef.PatientKey = pd.PatientKey
  join [CABOODLE_REPORT].[dbo].HospitalAdmissionFact                haf
    on icu.EncounterKey = haf.EncounterKey
  LEFT JOIN #ic_covid ic
    ON      ef.EncounterEpicCsn = ic.EncounterEpicCsn
            AND ic.CovidResolvedBounded > CrossIcuStayStartInstant
            AND ic.CovidOnsetInstant < 
                case when CrossIcuStayEndInstant is null
                then getdate() else CrossIcuStayEndInstant end --CrossIcuStayEndBounded
  left Join #WardMoves                                              wm
    ON      icu.IcuStayBlockId = wm.IcuStayBlockId
  WHERE
    icu.EncounterKey > 0
    AND icu.DepartmentKey not in (6387, 6382, 6385) -- EGA ICUs
    AND CensusLocationKey <> 1127 -- The PLEX Room on MITU
    AND NOT(CensusLocationKey = 31296 AND IcuLengthOfStay < 1) -- SR11 on MITU which is also home to many short lived stays
    AND pd.IsValid = 1 -- Excludes test patients
    AND IcuStayStartInstant > '2019-01-01' -- Well before the start of Epic
  ;

/************************* Granularity of Cross ICU Admission ***************************

Aggregates using the Cross ICU Stay Block ID
The treated_on_t06 metric is a sanity check for COVID status

*****************************************************************************************/
drop table if exists #crossicu;
drop table if exists #icuSeq;
select CrossIcuStayBlockId
            , IcuStayBlockId
            , Icu
            , [Site]
            , PrevDepartmentName
            , AdmittedFrom
            , AdmittedFromDeptType
            , NextDepartmentName
            , DischargedTo
            , RANK() OVER (PARTITION BY CrossIcuStayBlockId ORDER BY IcuStayStartInstant asc) as IcuStayOrder
            , RANK() OVER (PARTITION BY CrossIcuStayBlockId ORDER BY IcuStayStartInstant desc) as ReverseIcuStayOrder
into #icuSeq
from #icu;


with ward_seq as (
    select CrossIcuStayBlockId, 
           LEFT(t3.ward_sequence,Len(t3.ward_sequence)-1)               as icu_sequence
           , CASE WHEN t3.ward_sequence LIKE '%T06%' THEN 1 ELSE 0 END  as treated_on_t06
    from
        (
            select distinct t2.CrossIcuStayBlockId,
                (
                select t1.Icu + '; ' AS [text()], t1.AdmittedFrom + '; ' AS [text()]
                from #icu t1
                where t1.CrossIcuStayBlockId = t2.CrossIcuStayBlockId
                order by t1.CrossIcuStayBlockId,IcuStayStartInstant
                for XML PATH ('')
                ) ward_sequence
            from #icu t2
        ) t3
),

FirstStayDetails as (
    select CrossIcuStayBlockId
        , IcuStayBlockId            as FirstIcuStayBlockId
        , PrevDepartmentName
        , AdmittedFrom              as AdmittedFromCrossIcu
        , AdmittedFromDeptType      as AdmittedFromDeptTypeCrossIcu
        , Icu                       as FirstIcu
        , [Site]                    as FirstSite
    from #icuSeq i
    where i.IcuStayOrder = 1
),

LastStayDetails as (
    select CrossIcuStayBlockId
        , IcuStayBlockId            as LastIcuStayBlockId
        , NextDepartmentName
        , DischargedTo              as DischargedToCrossIcuStay
        , Icu                       as LastIcu
        , [Site]                    as LastSite
    from #icuSeq i
    where i.IcuStayOrder = 1
)


select -- Patient Demographics
      PatientKey
      ,PrimaryMrn
      ,NhsNumber
      ,FirstName
      ,LastName
      ,BirthDate
      ,min(AgeAtIcuStayStart)                                   AgeAtIcuAdmStart
      ,Sex
      ,Ethnicity

      -- ICU Stay Details
      , #icu.CrossIcuStayBlockId
      , CrossIcuStayStartInstant
      , CrossIcuStayEndInstant
      , CrossIcuStayEndBounded
      , datediff(DAY, CrossIcuStayStartInstant, CrossIcuStayEndBounded) CrossIcuLOS
      , fsd.PrevDepartmentName
      , fsd.AdmittedFromCrossIcu
      , fsd.AdmittedFromDeptTypeCrossIcu
      , fsd.FirstIcuStayBlockId
      , fsd.FirstSite
      , fsd.FirstIcu
      , icu_sequence
      , max(TreatedAtGWB)                                       TreatedAtGWB
      , max(TreatedAtQS)                                        TreatedAtQS
      , max(TreatedAtWMS)                                       TreatedAtWMS
      , max(TreatedAtUCH)                                       TreatedAtUCH
      , max(TreatedOnT06)                                       TreatedOnT06
      , lsd.LastIcuStayBlockId
      , lsd.LastSite
      , lsd.LastIcu
      ,lsd.NextDepartmentName
      , lsd.DischargedToCrossIcuStay
      , StatusAtCrossIcuStayEnd

      -- Encounter Details
      , EncounterEpicCsn
      , EncounterKey
      , AdmissionSource
      , AdmissionType
      , EncounterStartInstant
      , EncounterEndInstant
      , DischargeDestination
      , DischargeDisposition
      , DeathInstant

      -- COVID Status
      , CovidStatus
      , CovidOnsetInstant
      , CovidResolvedInstant
into #crossicu
from #icu
join ward_seq
    on #icu.CrossIcuStayBlockId = ward_seq.CrossIcuStayBlockId
join FirstStayDetails fsd
    on #icu.CrossIcuStayBlockId = fsd.CrossIcuStayBlockId
join LastStayDetails lsd
    on #icu.CrossIcuStayBlockId = lsd.CrossIcuStayBlockId
group by
      PatientKey
      ,PrimaryMrn
      ,NhsNumber
      ,FirstName
      ,LastName
      ,BirthDate
      ,Sex
      ,Ethnicity

      -- ICU Stay Details
      , #icu.CrossIcuStayBlockId
      , CrossIcuStayStartInstant
      , CrossIcuStayEndInstant
      , CrossIcuStayEndBounded
      , datediff(DAY, CrossIcuStayStartInstant, CrossIcuStayEndBounded)
      , fsd.PrevDepartmentName
      , fsd.AdmittedFromCrossIcu
      , fsd.AdmittedFromDeptTypeCrossIcu
      , fsd.FirstIcuStayBlockId
      , fsd.FirstSite
      , fsd.FirstIcu
      , icu_sequence
      , lsd.LastIcuStayBlockId
      , lsd.LastSite
      , lsd.LastIcu
      , lsd.DischargedToCrossIcuStay
      , lsd.NextDepartmentName
      , StatusAtCrossIcuStayEnd
      
      -- Encounter Details
      , EncounterEpicCsn
      , EncounterKey
      , AdmissionSource
      , AdmissionType
      , EncounterStartInstant
      , EncounterEndInstant
      , DischargeDestination
      , DischargeDisposition
      , DeathInstant

      -- COVID Status
      , CovidStatus
      , CovidOnsetInstant
      , CovidResolvedInstant    
order by
    CrossIcuStayStartInstant;






/************************* Transferred Patients ***************************
There are a number of different ways a transferred patient might be identified
- Admission Source = Other NHS Hospital
- Admission Type = Emergency Admission - Transfer of Admitted Patient from another Hospital Provider
- The prior department is NULL
- The Encounter Start and ICU Stay Start are identical

SQL for these conditions is below

AdmissionSource = 'Other NHS Hospital - Ward for General Patients, Younger Physically Disabled, or A&E'
OR AdmissionType = 'Emergency Admission - Transfer of Admitted Patient from another Hospital Provider'
OR pre_cross_icu_stay_department is null
OR DATEDIFF(MINUTE, EncounterStartInstant, CrossIcuStayStartInstant) = 0

Use of any of the criteria (ie: max sensitivity, min specificity) yields 206 CrossIcuStays
between '2021-04-01' and '2021-11-01'

Stats for the individual rules are listed below
AdmissionType = transfer: 122
pre_cross_icu_stay_department = null: 135
no difference between encounter and icu stay start time: 125

There is frequent logical disparity between Admission Method and Admission Source indicating that these
field are unreliable either alone or in combination.

Prior department is sometimes NULL for patients admitted from ED. Further investigation needed

The no difference between encounter and Cross ICU Stay Start seems pretty reliable.
Manual inspection of a handful where peior ward is NULL but there is a time difference between
Cross ICU Stay Start shows that when there is a gap of time there has usually been an error in 
recording the prior location.



select CrossIcuStayBlockId
    , EncounterEpicCsn
    , PrimaryMrn
    , NhsNumber
    , EncounterStartInstant
    , CrossIcuStayStartInstant
    , DATEDIFF(MINUTE, EncounterStartInstant, CrossIcuStayStartInstant) as encounter_to_icu_admit_diff_mins
    , CrossIcuStayEndInstant
    
    , AdmissionSource
    , AdmissionType
    , FirstIcuStayBlockId
    , FirstIcu
    , AdmittedFromCrossIcu
    , StatusAtCrossIcuStayEnd
    , TreatedOnT06
    , CovidStatus
from #crossicu icu
where
    (TreatedAtGWB = 1 OR TreatedAtUCH = 1 OR TreatedAtWMS = 1)
    and CrossIcuStayStartInstant between '2021-04-01' and '2021-11-01'
    and DATEDIFF(MINUTE, EncounterStartInstant, CrossIcuStayStartInstant) = 0
order by 
     StatusAtCrossIcuStayEnd, CrossIcuStayStartInstant asc
;

select * from #icuseq where IcuStayOrder > 1

select PrevDepartmentName from #icu where AdmittedFrom is null; --915
select * from #icu where DATEDIFF(MINUTE, EncounterStartInstant, IcuStayStartInstant) = 0; --815
select * from #icu 
where DATEDIFF(MINUTE, EncounterStartInstant, IcuStayStartInstant) <> 0
 and AdmittedFrom is  null;

 *****************************************************************************************/

 select
    icu.PatientKey
    ,icu.CrossIcuStayStartInstant
    ,icu.CrossIcuStayEndInstant
    ,icu.CrossIcuLOS
    ,FirstIcu
    ,LastIcu
    ,CovidStatus
    ,CovidOnsetInstant
    ,CovidResolvedInstant
 from #crossicu icu
 left join PatientDim pd
 on icu.PatientKey = pd.PatientKey
 where CrossIcuStayStartInstant >= '2021-01-01' 
    and FirstIcu = 'UCH T06 SOUTH PACU'
 order by CrossIcuStayStartInstant asc