class Python:
    code_1 = """
        import numpy as np
        
        def perform_bernoulli_trials(n, p):
        
            # Initialize number of successes: n_success
            n_success = 0
        
            # Perform trials
            for i in range(n):
                # Choose random number between zero and one: random_number
                random_number = np.random.random()
        
                # If less than p, it's a success so add one to n_success
                if random_number < p:
                    n_success += 1
        
            return n_success
        """

    code_2 = """
        import numpy as np
        def perform_bernoulli_trials(n, p):
        # Initialize number of successes: n_success
        n_success = 0
        return n_success
        """

    code_3 = """
        from sklearn.preprocessing import StandardScaler, OneHotEncoder
        import matplotlib.pyplot as plt
        import numpy as np
        import lib

        def perform_bernoulli_trials(n, p):
        
            # Initialize number of successes: n_success
            n_success = 0
            return n_success
            
        print("Python is great!")
        
        np.ndarray(size=(5,5))
        
        x = 5 * 3
        """

    code_4 = """
        import numpy as np
        n_success = 0
        print("Python is great!")
        """

    code_5 = """
        import matplotlib
        import numpy as np
        from sklearn.svm import SVC
        from sklearn.preprocessing import StandardScaler
        from sklearn.datasets import make_classification
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import Pipeline
        X, y = make_classification(random_state=0)
        X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)
        pipe = Pipeline([('scaler', StandardScaler()), ('svc', SVC())])
        # The pipeline can be used as any other estimator
        # and avoids leaking the test set into the train set
        pipe.fit(X_train, y_train)
        pipe.score(X_test, y_test)
        """

    code_6 = """
        import pandas as pd
        import matplotlib.pyplot as plt
        import numpy as np
        dataset = pd.read_csv('../input/Position_Salaries.csv')
        X = dataset.iloc[:, 1:2].values
        y = dataset.iloc[:, -1].values
        from sklearn.preprocessing import StandardScaler
        sc_X = StandardScaler()
        sc_Y = StandardScaler()
        X = sc_X.fit_transform(X)
        y = np.squeeze(sc_Y.fit_transform(y.reshape(-1, 1)))
        # the feature scaling will be done to both X and Y and still Y will remain the Vector
        from sklearn.svm import SVR
        regressor = SVR(kernel = 'rbf')
        regressor.fit(X, y)
        SVR(C=1.0, cache_size=200, coef0=0.0, degree=3, epsilon=0.1,
            gamma='auto_deprecated', kernel='rbf', max_iter=-1, shrinking=True,
            tol=0.001, verbose=False)
        y_pred = regressor.predict([[6.5]])
        y_pred = sc_Y.inverse_transform(y_pred)
        print(y_pred)
        """

    code_7 = """
        from sklearn.preprocessing import StandardScaler
        X_scaled = StandardScaler().fit_transform(X)
        pca = decomposition.PCA(n_components=2)
        X_pca_scaled = pca.fit_transform(X_scaled)
        print('Projecting %d-dimensional data to 2D' % X_scaled.shape[1])
        plt.figure(figsize=(12,10))
        plt.scatter(X_pca_scaled[:, 0], X_pca_scaled[:, 1], c=df['diagnosis'], alpha=0.7, s=40);
        plt.colorbar()
        plt.title('PCA projection')
        plt.style.use('seaborn-muted');
    """
    code_8 = """
        # Import required libraries:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from sklearn import linear_model
    # Read the CSV file :
    data = pd.read_csv(“Fuel.csv”)
    data.head()
    # Let’s select some features to explore more :
    data = data[[“ENGINESIZE”,”CO2EMISSIONS”]]
    # ENGINESIZE vs CO2EMISSIONS:
    plt.scatter(data[“ENGINESIZE”] , data[“CO2EMISSIONS”] , color=”blue”)
    plt.xlabel(“ENGINESIZE”)
    plt.ylabel(“CO2EMISSIONS”)
    plt.show()
    # Generating training and testing data from our data:
    # We are using 80% data for training.
    train = data[:(int((len(data)*0.8)))]
    test = data[(int((len(data)*0.8))):]
    # Modeling:
    # Using sklearn package to model data :
    regr = linear_model.LinearRegression()
    train_x = np.array(train[[“ENGINESIZE”]])
    train_y = np.array(train[[“CO2EMISSIONS”]])
    regr.fit(train_x,train_y)
    # The coefficients:
    print (“coefficients : “,regr.coef_) #Slope
    print (“Intercept : “,regr.intercept_) #Intercept
    # Plotting the regression line:
    plt.scatter(train[“ENGINESIZE”], train[“CO2EMISSIONS”], color=’blue’)
    plt.plot(train_x, regr.coef_*train_x + regr.intercept_, ‘-r’)
    plt.xlabel(“Engine size”)
    plt.ylabel(“Emission”)
    # Predicting values:
    # Function for predicting future values :
    def get_regression_predictions(input_features,intercept,slope):
     predicted_values = input_features*slope + intercept
     return predicted_values
    # Predicting emission for future car:
    my_engine_size = 3.5
    estimatd_emission = get_regression_predictions(my_engine_size,regr.intercept_[0],regr.coef_[0][0])
    print (“Estimated Emission :”,estimatd_emission)
    # Checking various accuracy:
    from sklearn.metrics import r2_score
    test_x = np.array(test[[‘ENGINESIZE’]])
    test_y_ = np.array(test[[‘CO2EMISSIONS’]])
    test_y = regr.predict(test_x)
    print(“Mean absolute error: %.2f” % np.mean(np.absolute(test_y_ — test_y)))
    print(“Mean sum of squares (MSE): %.2f” % np.mean((test_y_ — test_y) ** 2))
    print(“R2-score: %.2f” % r2_score(test_y_ , test_y) )"""

    code_9 = """
        import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    
    # plotting the fgiure
    plt.figure(figsize = (7,7))
    
    # assigning the input values
    X_set, y_set = X_train, y_train
    
    # ploting the linear graph
    X1, X2 = np.meshgrid(np.arange(start = X_set[:, 0].min() - 1, stop = X_set[:, 0].max() + 1, step = 0.01), np.arange(start = X_set[:, 1].min() - 1, stop = X_set[:, 1].max() + 1, step = 0.01))
    plt.contourf(X1, X2, classifier.predict(np.array([X1.ravel(), X2.ravel()]).T).reshape(X1.shape), alpha = 0.75, cmap = ListedColormap(('black', 'white')))
    plt.xlim(X1.min(), X1.max())
    plt.ylim(X2.min(), X2.max())
    
    # ploting scattered graph for the values
    for i, j in enumerate(np.unique(y_set)):
        plt.scatter(X_set[y_set == j, 0], X_set[y_set == j, 1], c = ListedColormap(('red', 'blue'))(i), label = j)
    
    # labeling the graph
    plt.title('Purchased Vs Non-Purchased')
    plt.xlabel('Salay')
    plt.ylabel('Age')
    plt.legend()
    plt.show()
        """

    code_10 = """
           from sklearn.datasets import load_iris
    iris = load_iris()
    
    # Model (can also use single decision tree)
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=10)
    
    # Train
    model.fit(iris.data, iris.target)
    # Extract single tree
    estimator = model.estimators_[5]
    
    from sklearn.tree import export_graphviz
    # Export as dot file
    export_graphviz(estimator, out_file='tree.dot', 
                    feature_names = iris.feature_names,
                    class_names = iris.target_names,
                    rounded = True, proportion = False, 
                    precision = 2, filled = True)
    
    # Convert to png
    from subprocess import call
    call(['dot', '-Tpng', 'tree.dot', '-o', 'tree.png', '-Gdpi=600'])
    
    # Display in python
    import matplotlib.pyplot as plt
    plt.figure(figsize = (14, 18))
    plt.imshow(plt.imread('tree.png'))
    plt.axis('off');
    plt.show();
    """

    code_11 = """
        from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaler.fit(df_feat)
    df_scaled = scaler.transform(df_feat)
    df_scaled = pd.DataFrame(df_scaled,columns=df_feat.columns[:4])
    df_preprocessed = pd.concat([df_scaled,dummies,target],axis=1)
    df_preprocessed.head()
        """
    code_12 = """
    from sklearn.cluster import KMeans
    from sklearn.metrics import confusion_matrix,classification_report,accuracy_score
    
    kmeans = KMeans(3,init='k-means++')
    kmeans.fit(df_preprocessed.drop('species',axis=1))
    print(confusion_matrix(df_preprocessed.species,kmeans.labels_))"""

    code_13 = """
        from sklearn.model_selection import train_test_split
    from sklearn.neighbors import KNeighborsClassifier
    
    # We need to split data for supervised learning models.
    X_train, X_test, y_train, y_test = train_test_split(df_preprocessed.drop('species',axis=1),target,test_size=0.50)
    
    knn = KNeighborsClassifier(n_neighbors=1)
    knn.fit(X_train,y_train)
    preds_knn = knn.predict(X_test)
    print(confusion_matrix(y_test,preds_knn))"""

    code_14 = """
    # explore gradient boosting number of trees effect on performance
    from numpy import mean
    from numpy import std
    from sklearn.datasets import make_classification
    from sklearn.model_selection import cross_val_score
    from sklearn.model_selection import RepeatedStratifiedKFold
    from sklearn.ensemble import GradientBoostingClassifier
    from matplotlib import pyplot
     
    # get the dataset
    def get_dataset():
        X, y = make_classification(n_samples=1000, n_features=20, n_informative=15, n_redundant=5, random_state=7)
        return X, y
     
    # get a list of models to evaluate
    def get_models():
        models = dict()
        # define number of trees to consider
        n_trees = [10, 50, 100, 500, 1000, 5000]
        for n in n_trees:
            models[str(n)] = GradientBoostingClassifier(n_estimators=n)
        return models
     
    # evaluate a given model using cross-validation
    def evaluate_model(model, X, y):
        # define the evaluation procedure
        cv = RepeatedStratifiedKFold(n_splits=10, n_repeats=3, random_state=1)
        # evaluate the model and collect the results
        scores = cross_val_score(model, X, y, scoring='accuracy', cv=cv, n_jobs=-1)
        return scores
     
    # define dataset
    X, y = get_dataset()
    # get the models to evaluate
    models = get_models()
    # evaluate the models and store results
    results, names = list(), list()
    for name, model in models.items():
        # evaluate the model
        scores = evaluate_model(model, X, y)
        # store the results
        results.append(scores)
        names.append(name)
        # summarize the performance along the way
        print('>%s %.3f (%.3f)' % (name, mean(scores), std(scores)))
    # plot model performance for comparison
    pyplot.boxplot(results, labels=names, showmeans=True)
    pyplot.show()
    """

    code_15 = """
    from sklearn.cluster import KMeans
    cs = []
    for i in range(1, 11):
        kmeans = KMeans(n_clusters = i, init = 'k-means++', max_iter = 300, n_init = 10, random_state = 0)
        kmeans.fit(X)
        cs.append(kmeans.inertia_)
    plt.plot(range(1, 11), cs)
    plt.title('The Elbow Method')
    plt.xlabel('Number of clusters')
    plt.ylabel('CS')
    plt.show()
    """

class R:
    code_1 = """
        library(ggplot2) # Data visualization
        library(readr) # CSV file I/O, e.g. the read_csv function
        library(sqldf)
        list.files("../input")
        print('Total runtime is ~2 mins')
        print('Importing train_2016 ... should be 90275')
        train_2016 <- read_csv("../input/train_2016_v2.csv", col_types = cols(transactiondate = col_skip(), parcelid = col_integer())); nrow(train_2016)
        print('Combining dupes (taking average) ... should be 90150')
        train_2016 <- sqldf('SELECT parcelid, avg(logerror) as logerror FROM train_2016 GROUP BY parcelid'); nrow(train_2016)
        print('Importing properties_2016 ... should be 2,985,217')
        properties_2016 <- read_csv("../input/properties_2016.csv", col_types = cols(parcelid = col_integer())); nrow(properties_2016)
        print('Combining train_2016 and properties_2016 ... should be 2,985,217')
        #alldata <- sqldf("SELECT * FROM properties_2016 LEFT JOIN train_2016 USING(parcelid)"); nrow(alldata)
        alldata <- merge(x = properties_2016, y = train_2016, by = "parcelid", all.x = TRUE)
        print('Building model ...')
        lr1 <- lm(logerror ~ fullbathcnt + calculatedfinishedsquarefeet + parcelid, data=alldata);
        summary(lr1) # view the model
        print('Making predictions ...')
        predictions <- data.frame(predict(lr1, alldata))
        print('Appending predictions to alldata ...')
        alldata$p_lr1 <- predictions$predict.lr1..alldata.
        alldata$p_lr1[is.na(alldata$p_lr1)] <- mean(alldata$logerror, na.rm = TRUE)  # Replace missing with average
        print('Average prediction value is ...')
        mean(alldata$p_lr1)
        print('Creating submission file')
        submit <- data.frame(alldata[,c("parcelid", "p_lr1")])
                      submit$"201610" <- round(submit$p_lr1,4)
                      submit$"201611" <- round(submit$p_lr1,4)
                      submit$"201612" <- round(submit$p_lr1,4)
                      submit$"201710" <- 0
                      submit$"201711" <- 0
                      submit$"201712" <- 0
        submit$p_lr1<- NULL # remove the original prediction from the submit file
        write.csv(submit, file = "submit_1.csv", row.names = FALSE, na="") # export the file for submission
        print('Done!')
        """

    code_2 = """
        library(tidyverse)
        list.files(path = "../input")
        #1-Import the data
        salary_data=read_csv("../input/salary-data-simple-linear-regression/Salary_Data.csv")
        #2-Summary and plot the data
        summary.data.frame(salary_data)
        plot(salary_data$YearsExperience,salary_data$Salary,xlab="Salary",ylab="Years of experience",main="Salary with respect to years of experience",col="blue")
        #3-Run the regression
        plot(salary_data$YearsExperience,salary_data$Salary, pch=16,cex=1.3, col="green",xlab="Years of experience",ylab="Salary",main="linear regression training set")
        lm=lm(Salary~YearsExperience,salary_data)
        summary(lm)
        abline(lm)
        plot(lm)
        """

    code_3  = """
    library(MASS)
    library(tidyverse)
    library(caret)
    
    # normalize data :
    all_data <- rbind(final_train[,-1],final_train_last[,-1],final_test[,-c(1,2)])
    preproc.param <- all_data %>% preProcess(method = c("center", "scale"))
    all_data.transformed <- preproc.param %>% predict(all_data)
    train.transformed <- all_data.transformed[1:15118,]
    validation.transformed <- all_data.transformed[15119:18717,]
    test.transformed <- all_data.transformed[18718:19717,]
    
    # I remove some variables because the lda method does not accept collinearity
    formule <- as.formula("accuracy_group~ accumulated_accuracy_group + dif_4070 + dif_2030 + duration_mean + dif_4030 + accumulated_uncorrect_attempts + Clip + + Chow_Time + somme_clip_game_activity + assessment_before_accuracy + accumulated_actions + acc_0 + acc_1 + acc_3 + acc_Bird + acc_Caul + acc_Mush + acc_Ches + acc_Cart + lgt_Caul + lgt_Mush + lgt_Ches + lgt_Cart + agt_Bird + agt_Caul + agt_Mush + agt_Ches + agt_Cart + ata_Bird + ata_Caul + ata_Mush + ata_Ches + ata_Cart + afa_Bird + afa_Caul + afa_Mush + afa_Ches + titre0 + titre1 + titre2 + titre3")
    # Fit the model
    model <- lda(formule, data = cbind(final_train[,1],train.transformed))"""

    code_4 = """
            install.packages("e1071")
    install.packages("caTools")
    install.packages("class")
      
    # Loading package
    library(e1071)
    library(caTools)
    library(class)
      
    # Loading data
    data(iris)
    head(iris)
      
    # Splitting data into train
    # and test data
    split <- sample.split(iris, SplitRatio = 0.7)
    train_cl <- subset(iris, split == "TRUE")
    test_cl <- subset(iris, split == "FALSE")
      
    # Feature Scaling
    train_scale <- scale(train_cl[, 1:4])
    test_scale <- scale(test_cl[, 1:4])
      
    # Fitting KNN Model 
    # to training dataset
    classifier_knn <- knn(train = train_scale,
                          test = test_scale,
                          cl = train_cl$Species,
                          k = 1)
    classifier_knn
      
    # Confusiin Matrix
    cm <- table(test_cl$Species, classifier_knn)
    cm
      
    # Model Evaluation - Choosing K
    # Calculate out of Sample error
    misClassError <- mean(classifier_knn != test_cl$Species)
    print(paste('Accuracy =', 1-misClassError))
      
    # K = 3
    classifier_knn <- knn(train = train_scale,
                          test = test_scale,
                          cl = train_cl$Species,
                          k = 3)
    misClassError <- mean(classifier_knn != test_cl$Species)
    print(paste('Accuracy =', 1-misClassError))
      
    # K = 5
    classifier_knn <- knn(train = train_scale,
                          test = test_scale,
                          cl = train_cl$Species,
                          k = 5)
    misClassError <- mean(classifier_knn != test_cl$Species)
    print(paste('Accuracy =', 1-misClassError))
      
    # K = 7
    classifier_knn <- knn(train = train_scale,
                          test = test_scale,
                          cl = train_cl$Species,
                          k = 7)
    misClassError <- mean(classifier_knn != test_cl$Species)
    print(paste('Accuracy =', 1-misClassError))
      
    # K = 15
    classifier_knn <- knn(train = train_scale,
                          test = test_scale,
                          cl = train_cl$Species,
                          k = 15)
    misClassError <- mean(classifier_knn != test_cl$Species)
    print(paste('Accuracy =', 1-misClassError))
      
    # K = 19
    classifier_knn <- knn(train = train_scale,
                          test = test_scale,
                          cl = train_cl$Species,
                          k = 19)
    misClassError <- mean(classifier_knn != test_cl$Species)
    print(paste('Accuracy =', 1-misClassError))
"""

    code_5 = """
    install.packages("caTools")    # For Logistic regression
install.packages("ROCR")       # For ROC curve to evaluate model
    
# Loading package
library(caTools)
library(ROCR) 
   
# Splitting dataset
split <- sample.split(mtcars, SplitRatio = 0.8)
split
   
train_reg <- subset(mtcars, split == "TRUE")
test_reg <- subset(mtcars, split == "FALSE")
   
# Training model
logistic_model <- glm(vs ~ wt + disp, 
                      data = train_reg, 
                      family = "binomial")
logistic_model
   
# Summary
summary(logistic_model)
   
# Predict test data based on model
predict_reg <- predict(logistic_model, 
                       test_reg, type = "response")
predict_reg  
   
# Changing probabilities
predict_reg <- ifelse(predict_reg >0.5, 1, 0)
   
# Evaluating model accuracy
# using confusion matrix
table(test_reg$vs, predict_reg)
   
missing_classerr <- mean(predict_reg != test_reg$vs)
print(paste('Accuracy =', 1 - missing_classerr))
   
# ROC-AUC Curve
ROCPred <- prediction(predict_reg, test_reg$vs) 
ROCPer <- performance(ROCPred, measure = "tpr", 
                             x.measure = "fpr")
   
auc <- performance(ROCPred, measure = "auc")
auc <- auc@y.values[[1]]
auc
   
# Plotting curve
plot(ROCPer)
plot(ROCPer, colorize = TRUE, 
     print.cutoffs.at = seq(0.1, by = 0.1), 
     main = "ROC CURVE")
abline(a = 0, b = 1)
   
auc <- round(auc, 4)
legend(.6, .4, auc, title = "AUC", cex = 1)
    """

    code_6 = """library(dplyr)
    # Drop variables
    clean_titanic <- titanic % > %
    select(-c(home.dest, cabin, name, X, ticket)) % > % 
    #Convert to factor level
        mutate(pclass = factor(pclass, levels = c(1, 2, 3), labels = c('Upper', 'Middle', 'Lower')),
        survived = factor(survived, levels = c(0, 1), labels = c('No', 'Yes'))) % > %
    na.omit()
    glimpse(clean_titanic)"""

    code_7 = """
    ImpData <- as.data.frame(importance(rf.fit))
    ImpData$Var.Names <- row.names(ImpData)
    
    ggplot(ImpData, aes(x=Var.Names, y=`%IncMSE`)) +
      geom_segment( aes(x=Var.Names, xend=Var.Names, y=0, yend=`%IncMSE`), color="skyblue") +
      geom_point(aes(size = IncNodePurity), color="blue", alpha=0.6) +
      theme_light() +
      coord_flip() +
      theme(
        legend.position="bottom",
        panel.grid.major.y = element_blank(),
        panel.border = element_blank(),
        axis.ticks.y = element_blank()
      )
"""

    code_8 = """set.seed(123)
valid_split <- initial_split(ames_train, .8)

# training data
ames_train_v2 <- analysis(valid_split)

# validation data
ames_valid <- assessment(valid_split)
x_test <- ames_valid[setdiff(names(ames_valid), "Sale_Price")]
y_test <- ames_valid$Sale_Price

rf_oob_comp <- randomForest(
  formula = Sale_Price ~ .,
  data    = ames_train_v2,
  xtest   = x_test,
  ytest   = y_test
)

# extract OOB & validation errors
oob <- sqrt(rf_oob_comp$mse)
validation <- sqrt(rf_oob_comp$test$mse)

# compare error rates
tibble::tibble(
  `Out of Bag Error` = oob,
  `Test error` = validation,
  ntrees = 1:rf_oob_comp$ntree
) %>%
  gather(Metric, RMSE, -ntrees) %>%
  ggplot(aes(ntrees, RMSE, color = Metric)) +
  geom_line() +
  scale_y_continuous(labels = scales::dollar) +
  xlab("Number of trees")
  """