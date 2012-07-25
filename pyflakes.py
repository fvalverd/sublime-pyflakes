# -*- coding: utf-8 -*-
import re
import subprocess

import sublime, sublime_plugin

PYFLAKES_REGION_NAME = 'PyflakesWarnings'
PYFLAKES_BINARY = 'pyflakes'


class PyflakesListener(sublime_plugin.EventListener):
  
  pyflakes_messages = dict()


  def on_load(self, view):
    self.exec_plugin(view)

  def on_post_save(self, view):
    self.exec_plugin(view)

  def on_selection_modified(self, view):
    if self.is_python_file(view):
      regions = view.get_regions(PYFLAKES_REGION_NAME)
      for region in regions:
        if region.contains(view.sel()[0]):
          self.show_status_bar_message_from_region(view.id(), region)
          break
  
  def exec_plugin(self, view):
    if self.is_python_file(view):
      view.erase_regions(PYFLAKES_REGION_NAME)
      self.pyflakes_messages[view.id()] = list()

      file_name = view.file_name().replace(' ', '\ ')
      process = subprocess.Popen([PYFLAKES_BINARY, file_name],
                  stdout=subprocess.PIPE)
      output, error = process.communicate()

      lines = list()
      for result in self.parse_pyflakes(output):
        line = self.line_from_line_number(view, result['line_number'])
        if line:
          self.add_pyflakes_messages(view.id(), line, result['text'])
          lines.append(line)

      self.set_markers_on_gutter(view, lines)

  def show_status_bar_message_from_region(self, view_id, region):
    for message in self.pyflakes_messages.get(view_id, list()):
      if message['region'] == region:
        sublime.status_message(message['text'])
        break

  def add_pyflakes_messages(self, view_id, line, text):
    self.pyflakes_messages[view_id].append({
        'region': line,
        'text': text,
      })


  @staticmethod
  def is_python_file(view):
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