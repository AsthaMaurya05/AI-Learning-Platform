"""
Machine Learning Models for Weak Area Detection and Prediction
Using: K-Means Clustering, Logistic Regression, Linear Regression
"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')


class WeakAreaClassifier:
    """
    Logistic Regression model to classify topics as Weak/Strong
    """
    
    def __init__(self):
        self.model = LogisticRegression(random_state=42)
        self.scaler = StandardScaler()
    
    def prepare_data(self, features_list):
        """
        Convert features to numpy arrays for sklearn
        """
        X = []
        y = []
        
        for features in features_list:
            # Feature vector: [accuracy, avg_time, trend, consistency]
            feature_vector = [
                features['accuracy'],
                features['avg_time'],
                features['trend'],
                features['consistency']
            ]
            X.append(feature_vector)
            
            # Label: 1 = Weak (accuracy < 60%), 0 = Strong
            label = 1 if features['accuracy'] < 60 else 0
            y.append(label)
        
        return np.array(X), np.array(y)
    
    def train(self, features_list):
        """
        Train the logistic regression model
        """
        if len(features_list) < 2:
            return None
        
        X, y = self.prepare_data(features_list)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Calculate accuracy
        y_pred = self.model.predict(X_scaled)
        train_accuracy = accuracy_score(y, y_pred)
        
        return {
            'accuracy': train_accuracy,
            'confusion_matrix': confusion_matrix(y, y_pred).tolist()
        }
    
    def predict(self, features):
        """
        Predict if a topic is weak (1) or strong (0)
        Returns: probability of being weak
        """
        feature_vector = np.array([[
            features['accuracy'],
            features['avg_time'],
            features['trend'],
            features['consistency']
        ]])
        
        feature_scaled = self.scaler.transform(feature_vector)
        
        # Get probability of being weak
        prob_weak = self.model.predict_proba(feature_scaled)[0][1]
        
        return prob_weak


class PerformanceClusterer:
    """
    K-Means Clustering to find performance patterns
    """
    
    def __init__(self, n_clusters=3):
        """
        3 clusters: Weak, Moderate, Strong
        """
        self.n_clusters = n_clusters
        self.model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.scaler = StandardScaler()
    
    def fit_predict(self, features_list):
        """
        Cluster topics into weak/moderate/strong groups
        """
        if len(features_list) < 3:
            return None
        
        X = []
        topics = []
        
        for features in features_list:
            feature_vector = [
                features['accuracy'],
                features['avg_time'],
                features['total_attempts']
            ]
            X.append(feature_vector)
            topics.append(features['topic'])
        
        X = np.array(X)
        X_scaled = self.scaler.fit_transform(X)
        
        # Perform clustering
        clusters = self.model.fit_predict(X_scaled)
        
        # Analyze cluster centers
        centers = self.scaler.inverse_transform(self.model.cluster_centers_)
        
        # Map clusters to labels (based on accuracy in cluster center)
        cluster_labels = {}
        for i, center in enumerate(centers):
            avg_accuracy = center[0]  # accuracy is first feature
            if avg_accuracy < 50:
                cluster_labels[i] = 'Weak'
            elif avg_accuracy < 70:
                cluster_labels[i] = 'Moderate'
            else:
                cluster_labels[i] = 'Strong'
        
        # Create results
        results = []
        for topic, cluster in zip(topics, clusters):
            results.append({
                'topic': topic,
                'cluster': int(cluster),
                'label': cluster_labels[cluster]
            })
        
        return {
            'clusters': results,
            'centers': centers.tolist(),
            'inertia': self.model.inertia_  # Sum of squared distances
        }


class ProgressPredictor:
    """
    Linear Regression to predict future performance
    """
    
    def __init__(self):
        self.model = LinearRegression()
    
    def train(self, session_data):
        """
        Train model on quiz session history
        session_data: list of {'session_number': int, 'accuracy': float}
        """
        if len(session_data) < 2:
            return None
        
        X = np.array([[s['session_number']] for s in session_data])
        y = np.array([s['accuracy'] for s in session_data])
        
        self.model.fit(X, y)
        
        # Calculate metrics
        y_pred = self.model.predict(X)
        mse = mean_squared_error(y, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y, y_pred)
        
        return {
            'mse': mse,
            'rmse': rmse,
            'r2_score': r2,
            'slope': self.model.coef_[0],  # Rate of improvement
            'intercept': self.model.intercept_
        }
    
    def predict(self, future_session_number):
        """
        Predict accuracy for a future session
        """
        X_future = np.array([[future_session_number]])
        prediction = self.model.predict(X_future)[0]
        
        # Cap prediction between 0-100
        prediction = max(0, min(100, prediction))
        
        return prediction