# MCA_Placement
This is a completed project submitted for Econ 484 and recieving a perfect score utilizing various ML techniques to determine likelihood of landing a job at one of the top 3 consultancy firms. With two exceptions, all methods are performed using the Sklearn machine learning API, whose userfriendliness comes at the tradeoff of performance seen in other APIs as TensorFlow.

Data is self reported from 2009-2021 membership of the BYU Management Consulting Association (MCA) detailing whether a student recieved a job offer from 1 of the top 3 consulting firms (outcome of interest) and various input features including GPA, ACT, Gender, firm location, and several binary variables: whether student has a business major (target variable), double major, minor, or an internship prior to offer. 

Although the source data is de-identified, it is not included for reasons of proprietary and confidentiality. Please contact me to arrange delivery of source data for purposes of replication or further study. 

You will notice that most of the algorithms utilize some form of double-debiased layer, which is used to establish causality rather than answer the typical predictive questions of these applications of ML.

Thank you for visiting. I would appreciate any feedback to improve the efficiency of these algorithms! 

~Collin

Abstract:

In this paper, we explore the causal relationship between BYU business school degrees and management consultancy offers at the three most prestigious global management consulting firms — McKinsey, BCG, and Bain (MBB). Our question is, “What is the causal effect of being a major in the business school on receiving an MBB job offer?” This question is important for 1) undergraduate students interested in working in the field of management consulting who are deciding on a college major and 2) undergraduate students in non-business majors who are deciding whether or not they want to put in the effort to recruit with MBB.
