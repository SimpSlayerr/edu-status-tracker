Run python tracker.py
  python tracker.py
  shell: /usr/bin/bash -e {0}
  env:
    pythonLocation: /opt/hostedtoolcache/Python/3.11.16/x64
    PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.16/x64/lib/pkgconfig
    Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.16/x64
    Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.16/x64
    Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.16/x64
    LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.16/x64/lib
    TELEGRAM_BOT_TOKEN: ***
    TELEGRAM_CHAT_ID: ***
    REG_NUMBER: ***
    APP_EMAIL: ***
  
Traceback (most recent call last):
1. Connecting to https://russia-edu.minobrnauki.gov.ru...
2. Filling form inputs...
  File "/home/runner/work/edu-status-tracker/edu-status-tracker/tracker.py", line 96, in <module>
3. Submitting form...
4. Waiting for details matching ***...
    execute_check()
  File "/home/runner/work/edu-status-tracker/edu-status-tracker/tracker.py", line 54, in execute_check
    page.locator(f"text={REG_NUMBER}").first.wait_for(timeout=30000)
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/site-packages/playwright/sync_api/_generated.py", line 20539, in wait_for
    self._sync(
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/site-packages/playwright/_impl/_sync_base.py", line 115, in _sync
    return task.result()
           ^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/site-packages/playwright/_impl/_locator.py", line 748, in wait_for
    await self._frame.wait_for_selector(
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/site-packages/playwright/_impl/_frame.py", line 394, in wait_for_selector
    await self._channel.send(
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/site-packages/playwright/_impl/_connection.py", line 76, in send
    return await self._connection.wrap_api_call(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/site-packages/playwright/_impl/_connection.py", line 632, in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("text=***").first to be visible
Error: Process completed with exit code 1.
