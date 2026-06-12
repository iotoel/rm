Get-ChildItem C:\rm -Recurse -File |
>> Where-Object { $_.FullName -notmatch "\\__pycache__\\" } |
>> ForEach-Object { "$($_.FullName)`n$((Get-Content $_.FullName -Raw))`n" }