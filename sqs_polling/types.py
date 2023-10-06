from typing import TypedDict

RedrivePolicy = TypedDict(
    "RedrivePolicy",
    {
        "deadLetterTargetArn": str,
        "maxReceiveCount": int,
    },
)
