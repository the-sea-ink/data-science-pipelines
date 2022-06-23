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
        score(X_test, y_test)
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
        library(tidyverse)
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