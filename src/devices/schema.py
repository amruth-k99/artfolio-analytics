from pydantic import BaseModel, ConfigDict


class DeviceTypesBase(BaseModel):
    os: str
    device_type: str
    browser: str


class DeviceTypesCreate(DeviceTypesBase):
    pass


class DeviceTypesRead(DeviceTypesBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
