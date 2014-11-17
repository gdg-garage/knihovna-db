import jinja2
import os

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    extensions=['jinja2.ext.autoescape'],
    trim_blocks=True,
    autoescape=True)


def render_html(request_handler, template, title, body, template_values=None):
    values = template_values if template_values is not None else {}
    values["title"] = title
    values["message"] = body
    template = JINJA_ENVIRONMENT.get_template(template)
    request_handler.response.write(template.render(values))


def render_txt(request_handler, template, values):
    jinja_template = JINJA_ENVIRONMENT.get_template(template)
    request_handler.response.headers['Content-Type'] = 'application/octet-stream'
    request_handler.response.write(jinja_template.render(values))