class ServiceResult:
    def __init__(self,is_success:bool,data=None,error_message=None,status=200):
        self.is_success=is_success
        self.data=data
        self.error_message=error_message
        self.status=status
    
    @staticmethod
    def as_success(data):
        return ServiceResult(True,data,None,200)
    @staticmethod
    def as_failure(error_message,status):
        return ServiceResult(False,None,error_message,status)

    def to_dict(self):
        return {
            "isSuccess": self.is_success,
            "data": self.data,
            "errorMessage": self.error_message,
            "status": self.status
        }   
             