import dataclasses
from enum import auto, IntEnum
from typing import List, Any, Dict, Union, Tuple


class SeparatorStyle(IntEnum):
    """Separator styles."""

    ADD_COLON_TWO = auto()
    DEFAULT = auto()


IMAGE_PLACEHOLDER_STR = "$$<image>$$"


@dataclasses.dataclass
class Conversation:
    """A class that manages prompt templates and keeps all conversation history."""

    # The name of this template
    name: str
    # The template of the system prompt
    system_template: str = "{system_message}"
    # The system message
    system_message: str = ""
    system_message_vision: str = ""
    # The names of two roles
    roles: Tuple[str] = ("USER", "ASSISTANT")
    # All messages. Each item is (role, message).
    # Each message is either a string or a tuple of (string, List[image_url]).
    messages: List[List[str]] = ()
    # The number of few shot examples
    offset: int = 0
    # The separator style and configurations
    sep_style: SeparatorStyle = SeparatorStyle.DEFAULT
    sep: str = "\n"
    sep2: str = None
    # Stop criteria (the default one is EOS token)
    stop_str: Union[str, List[str]] = None
    # Stops generation if meeting any token in this list
    stop_token_ids: List[int] = None

    def get_prompt(self) -> str:
        """Get the prompt for generation."""
        system_prompt = self.system_template.format(
            system_message=self.system_message
        )
        if self.sep_style == SeparatorStyle.ADD_COLON_TWO:
            seps = [self.sep, self.sep2]
            ret = system_prompt + seps[0]
            for i, (role, message) in enumerate(self.messages):
                if message:
                    if type(message) is tuple:
                        message, images = message
                        message = IMAGE_PLACEHOLDER_STR * len(images) + message
                    ret += role + ": " + message + seps[i % 2]
                else:
                    ret += role + ":"
            return ret
        elif self.sep_style == SeparatorStyle.DEFAULT:
            ret = system_prompt + "\n"
            for role, message in self.messages:
                if message:
                    if type(message) is tuple:
                        message, images = message
                    ret += role + ": " + message + "\n"
                else:
                    ret += role + ":"
            return ret
        else:
            raise ValueError(f"Invalid style: {self.sep_style}")
        
    def set_system_message(self, system_message: str):
        """Set the system message."""
        self.system_message = system_message

    def get_system_message(self, is_vision=False):
        """return the system message."""
        if is_vision and self.system_message_vision:
            return self.system_message_vision
        return self.system_message

    def append_message(self, role: str, message: str):
        """Append a new message."""
        self.messages.append([role, message])

    def update_last_message(self, message: str):
        """Update the last output.

        The last message is typically set to be None when constructing the prompt,
        so we need to update it in-place after getting the response from a model.
        """
        self.messages[-1][1] = message

    def copy(self):
        return Conversation(
            name=self.name,
            system_template=self.system_template,
            system_message=self.system_message,
            system_message_vision=self.system_message_vision,
            roles=self.roles,
            messages=[[x, y] for x, y in self.messages],
            offset=self.offset,
            sep_style=self.sep_style,
            sep=self.sep,
            sep2=self.sep2,
            stop_str=self.stop_str,
            stop_token_ids=self.stop_token_ids,
        )

    def dict(self):
        return {
            "template_name": self.name,
            "system_message": self.system_message,
            "roles": self.roles,
            "messages": self.extract_text_and_image_hashes_from_messages(),
            "offset": self.offset,
        }


# A global registry for all conversation templates
conv_templates: Dict[str, Conversation] = {}


def register_conv_template(template: Conversation, override: bool = False):
    """Register a new conversation template."""
    if not override:
        assert (
            template.name not in conv_templates
        ), f"{template.name} has been registered."

    conv_templates[template.name] = template


def get_conv_template(name: str) -> Conversation:
    """Get a conversation template."""
    return conv_templates[name].copy()


# Vicuna v1.1 template
register_conv_template(
    Conversation(
        name="lmsys/vicuna-7b-v1.5",
        system_message="A chat between a curious user and an artificial intelligence assistant. "
        "The assistant gives helpful, detailed, and polite answers to the user's questions.",
        roles=("USER", "ASSISTANT"),
        sep_style=SeparatorStyle.ADD_COLON_TWO,
        sep=" ",
        sep2="</s>",
    )
)
