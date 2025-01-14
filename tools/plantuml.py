"""
title: PlantUML diagram generator
author: crooy
description: This tool creates pretty diagram image from PlantUML code
author_url: https://github.com/crooy/openwebui-things
version: 0.1
required_open_webui_version: 0.5.0
requirements: plantuml
"""

from typing import Any, Awaitable, Callable, Optional

from plantuml import PlantUML
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        """Configuration valves for the PlantUML tool"""
        plantuml_server: str = Field(
            default="http://www.plantuml.com/plantuml/img/",
            description="PlantUML server URL for image generation",
        )

    def __init__(self) -> None:
        self.valves: Tools.Valves = self.Valves()

    def __getattr__(self, name: str) -> Any:
        """Handle dynamic attribute access"""
        return getattr(self.valves, name)

    def generate_diagram(
        self,
        data: str,
        __user__: dict,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> str:
        """
        Create a pretty diagram in PNG image format from PlantUML code

        :param data: block of valid PlantUML code
        :param __user__: user dictionary
        :param __event_emitter__: event emitter callback
        :return: Markdown image link
        """
        print("generating diagram using plantuml server:", self.valves.plantuml_server)
        print("data:", data)

        if not data:
            return "Error: No PlantUML code provided"

        try:
            if not data.strip().startswith("@startuml"):
                data = "@startuml\n" + data
            if not data.strip().endswith("@enduml"):
                data = data + "\n@enduml"

            # Use PlantUML library to get URL
            plantuml = PlantUML(url=self.valves.plantuml_server)
            try:
                image_url = plantuml.get_url(data)
            except Exception as e:
                return f"Error generating PlantUML URL: {str(e)}"

            print("image_url:", image_url)

            return f"Notify the user that you created a diagram [Generated Diagram]({image_url}), it would be nice to include the image inline in the response. Copy the image url verbatim!!"

        except Exception as e:
            return f"There was an error in the PlantUML input code, please try again. Error: {str(e)}"
