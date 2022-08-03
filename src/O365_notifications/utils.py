import typing

import O365.mailbox
from marshmallow import Schema


def build_url(resource: O365.utils.ApiComponent) -> typing.Optional[str]:
    if isinstance(resource, O365.mailbox.Folder):
        folder = resource
        endpoints = folder._endpoints
        return folder.build_url(
            endpoints.get("folder_messages").format(id=folder.folder_id)
            if folder else endpoints.get("root_messages")
        )

    # TODO: complete this check sequence as needed

    return None


class DeserializerSchema(Schema):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for field in self.declared_fields.values():
            field.load_only = True
