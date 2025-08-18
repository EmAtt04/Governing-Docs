Get-Content installed-packages.txt |
    ForEach-Object {
        if ($_ -match '^i (\S+):') {
            $pkg = $matches[1]
            tlmgr install $pkg
        }
    }
