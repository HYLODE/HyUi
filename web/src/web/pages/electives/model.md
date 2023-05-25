# Model Card: PACU Bed Requirement

This page uses an experimental machine learning model to predict whether or not a patient will require admission to an Intensive Care Unit after their operation.

It is has not been tested nor validated and so should _not_ be used to guide clinical practice.

Currently, you can alter the cut-offs for when the model flags patients by moving the slider below.
The model will flag patients who are not booked for PACU but have **high** predicted probability of ICU admission by adding a ⚠️ flag to the PACU column. If a patient has a PACU bed booked but the predicted probability of ICU admission is **low**, the model will add a 🤷 symbol.

The **"high"** and **"low"** cut offs can be adjusted by moving the slider below.

We are keen to collect feedback on the performance of this model. Please contact our team at [h.vaidya@nhs.net](mailto:h.vaidya@nhs.net) to get involved.

## Model Details

### Model description
* **Developed by:**
* **Model type:** XGBoost Classifier
* **License:**

### Model Sources
* **Repository:**

## Uses
## Bias, Risks, and Limitations

## Training Details
### Training Data
### Training Procedure
## Technical Specifications

## Evaluation
### Testing Data, Factors, and Metrics
### Results
### Ongoing monitoring

## Citation
## More Information
