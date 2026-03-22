from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pdm.cli.commands.base import verbose_option
from pdm.cli.commands.init import Command as InitCommand

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from pdm.project import Project


class Command(InitCommand):
    """Create a new Python project at <project_path>"""

    supports_other_generator = False

    arguments = (verbose_option,)

    def add_arguments(self, parser: ArgumentParser) -> None:
        super().add_arguments(parser)
        parser.add_argument("project_path", help="The path to create the new project")

    def handle(self, project: Project, options: Namespace) -> None:
        new_project = project.core.create_project(
            options.project_path, global_config=options.config or os.getenv("PDM_CONFIG_FILE")
        )
        return super().handle(new_project, options)
