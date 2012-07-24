# -*- coding: utf-8 -*-
import re
import subprocess

import sublime, sublime_plugin

def is_python_file(view):
  return bool(re.search('Python', view.settings().get('syntax'), re.I))

LOG_TAG = "Pyflakes Plugin"

class PyflakesListener(sublime_plugin.EventListener):
  
  # TODO: change to {}
  pyflakes_messages = []

  
  # Overwrite sublime_plugin.EventListener

  def on_load(self, view):
    print LOG_TAG, "on_load"
    self.exec_plugin(view)

  def on_post_save(self, view):
    print LOG_TAG, "on_post_save"
    self.exec_plugin(view)

  def on_selection_modified(self, view):
    print LOG_TAG, "on_selection_modified"
    if is_python_file(view):
      regions = view.get_regions('PyflakesWarnings')
      for region in regions:
        if region.contains(view.sel()[0]):
          print LOG_TAG, view.sel()
          self.highlight_warning(region)
          break
  
  @staticmethod
  def parse_pyflakes(output):
    results = []
    if output:
      for raw_line in output.split('\n'):
        if raw_line:
          raw_line = raw_line[(raw_line.find(':') + 1):]
          line_number, text = raw_line.split(':')
          line_number = int(line_number) - 1
          text = text.strip()
          results.append({
            "line_number" : line_number,
            "text" : text,
          })
    return results

  def exec_plugin(self, view):
    if is_python_file(view):
      view.erase_regions('PyflakesWarnings')
      self.pyflakes_messages = []

      file_name = view.file_name().replace(' ', '\ ')
      process = subprocess.Popen(['pyflakes', file_name], stdout = subprocess.PIPE)
      output, error = process.communicate()

      lines = []
      for result in self.parse_pyflakes(output):
        line = self.get_line_error_from_pyflakes_output(view, result['line_number'])
        if line:
          self.add_pyflakes_messages(line, result['text'])
          lines.append(line)

      self.set_markers_on_gutter(view, lines)

  def highlight_warning(self, region):
    for message in self.pyflakes_messages:
      if message['region'] == region:
        print LOG_TAG, "Show dialog", message['text']
        sublime.status_message(message['text'])
        break

  def get_line_error_from_pyflakes_output(self, view, line_number):
    point = view.text_point(line_number, 0)
    line = view.line(point)
    return line

  def add_pyflakes_messages(self, line, text):
    self.pyflakes_messages.append({
        'region': line,
        'text': text,
      })
  
  @staticmethod
  def set_markers_on_gutter(view, regions):
    view.add_regions('PyflakesWarnings', regions, 'string pyflakeswarning', 'dot')