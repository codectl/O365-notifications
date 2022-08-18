import typing
from dataclasses import dataclass, fields

import O365.mailbox
from marshmallow import Schema, post_load


def build_url(resource: O365.utils.ApiComponent) -> typing.Optional[str]:
    if isinstance(resource, O365.mailbox.Folder):
        folder = resource
        endpoints = folder._endpoints
        return folder.build_url(
            endpoints.get("folder_messages").format(id=folder.folder_id)
            if folder
            else endpoints.get("root_messages")
        )

    # TODO: complete this check sequence as needed
    return None


@dataclass
class DeserializerMixin:
    raw: dict

    class DeserializerSchema(Schema):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            for f in self.declared_fields.values():
                f.load_only = True

        @post_load(pass_original=True)
        def include_raw_field(self, data, original_data, **_):
            data["raw"] = original_data
            return data

    schema = DeserializerSchema  # alias

    @classmethod
    def deserialize(cls, data: dict, **kwargs):
        cls_fields = [f.name for f in fields(cls)]
        loaded_fields = cls.schema(**kwargs).load(data)
        return cls(**{k: v for k, v in loaded_fields.items() if k in cls_fields})
