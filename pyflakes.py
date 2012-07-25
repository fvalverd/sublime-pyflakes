# -*- coding: utf-8 -*-
import re
import subprocess

import sublime_plugin


PYFLAKES_REGION_NAME = 'PyflakesWarnings'
PYFLAKES_BINARY = 'pyflakes'


class PyflakesListener(sublime_plugin.EventListener):
  
  pyflakes_messages = dict()
  pyflakes_status_bar_current_key = dict()


  # sublime_plugin.EventListener

  def on_load(self, view):
    if self.is_python_view(view):
      self.exec_plugin(view)

  def on_post_save(self, view):
    if self.is_python_view(view):
      self.exec_plugin(view)

  def on_close(self, view):
    if self.is_python_view(view):
      view_id = view.id()
      if view_id in self.pyflakes_messages:
        del self.pyflakes_messages[view.id()]
      if view_id in self.pyflakes_status_bar_current_key:
        del self.pyflakes_status_bar_current_key[view.id()]

  def on_selection_modified(self, view):
    if self.is_python_view(view):
      regions = view.get_regions(PYFLAKES_REGION_NAME)
      for region in regions:
        if region.contains(view.sel()[0]):
          self.set_status_bar_message_from_region(view, region)
          break
  

  # PyflakesListener

  def exec_plugin(self, view):
    self.clear_regions(view)
    output, error = self.run_pyflakes(view.file_name())

    lines = list()
    for result in self.parse_pyflakes(output):
      line = self.line_from_line_number(view, result['line_number'])
      if line:
        self.add_pyflakes_messages(view.id(), line, result['text'])
        lines.append(line)

    if (len(lines) > 0):
      self.set_markers_on_gutter(view, lines)

  def clear_regions(self, view):
    view.erase_regions(PYFLAKES_REGION_NAME)
    self.pyflakes_messages[view.id()] = list()
    self.clear_status_bar(view)

  def clear_status_bar(self, view):
    current_key = self.pyflakes_status_bar_current_key.get(view.id())
    if current_key:
      view.erase_status(current_key)
    self.pyflakes_status_bar_current_key[view.id()] = None

  def set_status_bar(self, view, text):
    self.clear_status_bar(view)
    view.set_status(text, text)
    self.pyflakes_status_bar_current_key[view.id()] = text

  def set_status_bar_message_from_region(self, view, region):
    for message in self.pyflakes_messages.get(view.id(), list()):
      if message['region'] == region:
        self.set_status_bar(view, message['text'])
        break

  def add_pyflakes_messages(self, view_id, line, text):
    self.pyflakes_messages[view_id].append({
        'region': line,
        'text': text,
      })

  @staticmethod
  def run_pyflakes(file_name):
    file_name = file_name.replace(' ', '\ ')
    process = subprocess.Popen([PYFLAKES_BINARY, file_name],
                stdout=subprocess.PIPE)
    return process.communicate()

  @staticmethod
  def is_python_view(view):
    return bool(re.search('Python',
                  view.settings().get('syntax'),
                  re.I))

  @staticmethod
  def parse_pyflakes(output):
    results = list()
    if output:
      for raw_line in output.split('\n'):
        if raw_line:
          raw_line = raw_line[(raw_line.find(':') + 1):]
          line_number, text = raw_line.split(':')
          line_number = int(line_number) - 1
          text = text.strip()
          results.append({
            'line_number' : line_number,
            'text' : text,
          })
    return results

  @staticmethod
  def line_from_line_number(view, line_number):
    point = view.text_point(line_number, 0)
    line = view.line(point)
    return line

  @staticmethod
  def set_markers_on_gutter(view, regions):
    view.add_regions(PYFLAKES_REGION_NAME,
      regions,
      'string pyflakeswarning',
      'dot')