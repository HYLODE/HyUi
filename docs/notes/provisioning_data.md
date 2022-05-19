## Provisioning data at UCLH

Data access at UCLH must overcome two barriers: permissions and provisioning. Permissions (research ethics etc.) are arduous but clear, and (rightly) the responsibility of the researcher.
But at UCLH, we are stuck on the *provisioning* step. This is because the researcher (the data consumer) and the hospital (the provider) are separate entities. The researcher is supposed to provide a precise data specification. The  hospital is supposed to extract and anonymise.

This is possible for small studies, but slow, expensive and eventually impossible  for Machine Learning for Health (ML4H). Here data requirements are established iteratively and cannot be specified a priori. Typically a researcher must first explore the full data set, and then works alongside domain experts (i.e. the clinical team) to build features from the data that serve the modelling task. Full anonymisation is a specialist skill not widely available among researchers or hospital data teams. Most extracts are de-identified not anonymised, but even this blocks future attempts to test models in the clinical environment since model predictions cannot be linked back to patients.[^1]

Data provisioning currently divides these tasks between researchers and the hospital, and runs them sequentially:
1. Requirement specification [researcher]
2. Extraction and anonymisation [hospital]
3. Model building [researcher]
4. Model deployment [hospital]

Neither side has the resources to support this properly. At present, there are only two full time data engineers in the CRIU but even a large team could not compete with the domain knowledge and efficiency of a researcher-clinician dyad.

We need instead a model that sees the provider/consumer roles merged. A sketch of the arrangement follows:
1. The CRIU would maintain a pseudonymised view of the commonest data sources in the trust (Epic reporting data warehouses, EMAP etc.). Access would be layered so that higher risk items such as free text required separate permissions. [Safe data]
2. Researchers would be required to follow a similar training to existing substantive NHS staff working with patient data (e.g. those in information services) or even held to a higher standard (e.g. as per the ONS approved researcher scheme). They would work under the supervision and line management of CRIU staff with an (honorary) contractual relationship to the hospital.[Safe People]
3. Data extraction and analysis would occur in the hospital but be performed by the research team using the pseudonymised data. [Safe setting]
4. The CRIU would maintain a two layer platform (as per Nel Swanepoel's FlowEHR architecture) that allows research models trained on pseudonymised data to be deployed against identifiable data. This would enable ML4H algorithms to be tested in the clinical environment without the researchers needing access to identifiable data.

This proposal follows both the Five Safes principles, and is similar to Precedent 3 under the guidance issued by the Confidential Advisory Group: "*accessing data on-site to extract anonymised data*". Under the Five Safes, we are offsetting a reduction in the safety of the data (de-identified rather than anonymised) by increasing the safety of the people, the setting and the outputs. Precedent 3 recognises that data preparation by researchers is legitimate when it is not practicable for the direct care team to fulfil that role.
We have already taken this approach to the BRC PPI panel on the use of data, and explicitly discussed this trade-off between the 'Five Safes'.  The technical work to pseudonymise existing health data is manageable, and we have a working implementation of the development/deployment platform.
The next step had been to take a version of this proposal to the trust information governance team for comment.

[^1]:	Difficulties in deployment are also the Achilles heel of a Trusted Research Environment. Whilst safe, these walled gardens mean that models are developed offline without the benefit of clinical testing.
