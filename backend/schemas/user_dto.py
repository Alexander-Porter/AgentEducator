from pydantic import BaseModel, validator

class UserLoginDTO(BaseModel):
    email: str
    password: str

class UserRegisterDTO(BaseModel):
    username: str
    email: str
    password: str
    role: str = "student"  # 默认为student角色
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ["student", "teacher"]
        if v not in valid_roles:
            raise ValueError(f"角色必须是 {', '.join(valid_roles)} 中的一个")
        return v