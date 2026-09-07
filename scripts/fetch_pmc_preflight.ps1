param(
    [int]$Count = 20,
    [int]$CandidateLimit = 200
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$DatasetRoot = Join-Path $ProjectRoot "data\raw\pubtables"
$DetectionRoot = Join-Path $DatasetRoot "PubTables-1M-Image_Page_Detection_PASCAL_VOC"
$SplitFile = Join-Path $DetectionRoot "val_filelist.txt"
$PdfRoot = Join-Path $DatasetRoot "pdfs"
$ManifestPath = Join-Path $DatasetRoot "pmc_preflight_manifest.json"
$PreflightSplitPath = Join-Path $DetectionRoot "preflight_filelist.txt"

if (-not (Test-Path -LiteralPath $SplitFile)) {
    throw "Missing PubTables validation file list: $SplitFile"
}

New-Item -ItemType Directory -Force -Path $PdfRoot | Out-Null
$splitLines = Get-Content -LiteralPath $SplitFile
$ids = $splitLines |
    ForEach-Object {
        if ($_ -match "(PMC\d+)_\d+\.xml$") { $Matches[1] }
    } |
    Select-Object -Unique -First $CandidateLimit

$rows = @()
foreach ($id in $ids) {
    if (($rows | Where-Object status -eq "downloaded").Count -ge $Count) { break }
    $target = Join-Path $PdfRoot "$id.pdf"
    if (Test-Path -LiteralPath $target) {
        $rows += [ordered]@{
            pmcid = $id
            status = "downloaded"
            source_url = $null
            local_path = $target
            bytes = (Get-Item -LiteralPath $target).Length
            reused = $true
        }
        continue
    }
    try {
        $listingUrl = "https://pmc-oa-opendata.s3.amazonaws.com/?list-type=2&prefix=$id."
        [xml]$listing = (Invoke-WebRequest -Uri $listingUrl).Content
        $keys = @(
            $listing.SelectNodes("//*[local-name()='Key']") |
                ForEach-Object { $_.InnerText } |
                Where-Object { $_ -match "\.pdf$" } |
                Sort-Object -Descending
        )
        if ($keys.Count -eq 0) {
            $rows += [ordered]@{ pmcid = $id; status = "no_pdf"; source_url = $null }
            continue
        }
        $key = $keys[0]
        $sourceUrl = "https://pmc-oa-opendata.s3.amazonaws.com/$key"
        Invoke-WebRequest -Uri $sourceUrl -OutFile $target
        $stream = [System.IO.File]::OpenRead($target)
        try {
            $header = New-Object byte[] 4
            [void]$stream.Read($header, 0, 4)
        }
        finally {
            $stream.Dispose()
        }
        if ([System.Text.Encoding]::ASCII.GetString($header) -ne "%PDF") {
            throw "Downloaded object is not a PDF"
        }
        $rows += [ordered]@{
            pmcid = $id
            status = "downloaded"
            source_url = $sourceUrl
            local_path = $target
            bytes = (Get-Item -LiteralPath $target).Length
            reused = $false
        }
        Write-Output "$id $((Get-Item -LiteralPath $target).Length) bytes"
    }
    catch {
        $rows += [ordered]@{
            pmcid = $id
            status = "error"
            error = $_.Exception.Message
        }
    }
    Start-Sleep -Milliseconds 250
}

$payload = [ordered]@{
    source = "NIH NLM PMC Article Datasets on AWS"
    bucket = "pmc-oa-opendata"
    retrieved_at_utc = [DateTime]::UtcNow.ToString("o")
    requested_count = $Count
    downloaded_count = ($rows | Where-Object status -eq "downloaded").Count
    rows = $rows
}
$payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ManifestPath -Encoding utf8
$downloadedIds = @($rows | Where-Object status -eq "downloaded" | ForEach-Object pmcid)
$preflightRows = foreach ($id in $downloadedIds) {
    $splitLines | Where-Object { $_ -match "^val/$id" + "_\d+\.xml$" } | Select-Object -First 1
}
$preflightRows | Set-Content -LiteralPath $PreflightSplitPath -Encoding utf8
Write-Output "manifest=$ManifestPath downloaded=$($payload.downloaded_count)"
Write-Output "split=$PreflightSplitPath rows=$($preflightRows.Count)"
if ($payload.downloaded_count -lt $Count) {
    throw "Only $($payload.downloaded_count) of $Count PDFs were acquired."
}
