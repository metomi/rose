import os
import tempfile

import sphinx
from sphinx.directives.code import CodeBlock
from docutils.parsers.rst.directives.images import Image
from docutils.parsers.rst import directives
from gvanim import Animation, render, gif


class MiniCylc(Image):
    has_content = True
    required_arguments = 0
    option_spec = dict(Image.option_spec)
    option_spec['snippet'] = directives.flag

    @staticmethod
    def make_animation(content):
        # Generate edges.
        tasks = set([])
        edges = []
        for line in content:
            items = line.split('=>')
            for left, right in zip(items, items[1:]):
                left = left.strip()
                right = right.strip()
                edges.append((left, right))
                tasks.add(left)
                tasks.add(right)

        # Define task pool.
        waiting = set(tasks)
        running = set([])
        succeeded = set([])

        # Draw first frame.
        anim = Animation()
        for left, right in edges:
            anim.add_edge(left, right)
        anim.next_step()

        # Run schedule.
        while waiting:
            for task in list(running):
                running.remove(task)
                succeeded.add(task)
            for task in list(waiting):
                can_run = True
                for left, right in edges:
                    if right == task:
                        if left not in succeeded:
                            can_run = False
                if can_run:
                    waiting.remove(task)
                    running.add(task)
            for left, right in edges:
                anim.add_edge(left, right)
            for task in running:
                anim.highlight_node(task)
            anim.next_step()

        # Render animation.
        tempdir = tempfile.mkdtemp()
        filebase = os.path.join(tempdir, 'render')
        graphs = anim.graphs()
        files = render(graphs, filebase, 'png')
        gif(files, filebase, 100)

        # Return gif file.
        return '/' + filebase + '.gif'  # TODO

    def run(self):
        filename = self.make_animation(self.content)
        self.arguments = [filename]
        if 'snippet' in self.options:
            return CodeBlock(self.name,
                             ['bash'],  # Arguments.
                             {},  # Options.
                             self.content,
                             self.lineno,
                             self.content_offset,
                             self.block_text,
                             self.state,
                             self.state_machine
                            ).run() + Image.run(self)
        return Image.run(self)


def setup(app):
    app.add_directive('minicylc', MiniCylc)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
