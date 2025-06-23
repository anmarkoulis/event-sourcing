from typing import Dict
from .base import BaseMappings, MappedField, get_date_time, get_date, get_list_from_string


class ClientMappings(BaseMappings):
    """Field mappings for Client (Account) entity"""
    
    @staticmethod
    def get_mappings() -> Dict[str, MappedField]:
        return {
            "id": MappedField("Id", lambda rec, _: rec["Id"]),
            "name": MappedField("Name", lambda rec, _: rec["Name"]),
            "parent_id": MappedField("ParentId", lambda rec, _: rec.get("ParentId", None)),
            "business_types": MappedField("Business_Type__c", get_list_from_string),
            "status": MappedField("Account_Status__c", lambda rec, _: rec.get("Account_Status__c")),
            "currency": MappedField("CurrencyIsoCode", lambda rec, _: rec.get("CurrencyIsoCode")),
            "billing_country": MappedField("BillingCountry", lambda rec, _: rec.get("BillingCountry")),
            "priority": MappedField("Account_Priority__c", lambda rec, _: rec.get("Account_Priority__c")),
            "sso_id": MappedField("Orfium_SSO_ID_Comp__c", lambda rec, _: rec.get("Orfium_SSO_ID_Comp__c") or rec.get("Orfium_SSO_ID_SR__c")),
            "sso_id_c": MappedField("Orfium_SSO_ID_Comp__c", lambda rec, _: rec.get("Orfium_SSO_ID_Comp__c")),
            "sso_id_r": MappedField("Orfium_SSO_ID_SR__c", lambda rec, _: rec.get("Orfium_SSO_ID_SR__c")),
            "description": MappedField("Description", lambda rec, _: rec.get("Description")),
            "is_deleted": MappedField("IsDeleted", lambda rec, _: rec.get("IsDeleted")),
            "last_modified_date": MappedField("LastModifiedDate", get_date_time),
            "system_modified_stamp": MappedField("SystemModstamp", get_date_time),
            "last_activity_date": MappedField("LastActivityDate", get_date),
            "created_date": MappedField("CreatedDate", get_date_time),
        } 