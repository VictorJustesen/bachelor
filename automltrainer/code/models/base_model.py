from abc import ABC, abstractmethod

class BaseModelConfig(ABC):
    
    @abstractmethod
    def get_model(self, **kwargs):
        pass
    
    @abstractmethod
    def get_param_grid(self, grid_type):
        pass
    
    @abstractmethod
    def get_model_name(self):
        pass
    
    def get_default_configs(self):
        return {
            f'{self.get_model_name()}_quick': self.get_param_grid('quick'),
            f'{self.get_model_name()}_full': self.get_param_grid('full'),
            f'{self.get_model_name()}_conservative': self.get_param_grid('conservative')
        }
    
    def train_and_predict(self, X_train, y_train, X_test, loss_fn=None, **model_params):
        
        model = self.get_model(loss_fn=loss_fn, **model_params)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        
        return model, y_pred

    @abstractmethod
    def save_model(self, filepath):
      
        return None  