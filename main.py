name: Daily Tsume Shogi

on:
  schedule:
    # 日本時間の朝7時に実行 (UTCの22時を指定)
    - cron: '0 22 * * *'
  workflow_dispatch: # 手動実行テスト用

jobs:
  run-shogi-script:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests beautifulsoup4

    - name: Run script
      env:
        GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
      run: python main.py
