$ErrorActionPreference = 'Stop'
$ReportDirectory = $PSScriptRoot
$HtmlPath = Join-Path $ReportDirectory 'TAKG_reproduction_report.html'
$DocxPath = Join-Path $ReportDirectory 'TAKG_reproduction_report.docx'
$PdfPath = Join-Path $ReportDirectory 'TAKG_reproduction_report.pdf'

if (-not (Test-Path -LiteralPath $HtmlPath)) {
    throw "Report HTML not found: $HtmlPath"
}

$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($HtmlPath, $false, $false)

    # Word 2007+ default XML document (.docx).
    $document.SaveAs($DocxPath, 16)

    # Add quiet page numbers after conversion and save once more.
    foreach ($section in $document.Sections) {
        $footer = $section.Footers.Item(1)
        $footer.Range.ParagraphFormat.Alignment = 2
        if ($footer.PageNumbers.Count -eq 0) {
            [void]$footer.PageNumbers.Add(2, $true)
        }
    }
    $document.Save()

    # wdExportFormatPDF = 17, optimized for print = 0.
    $document.ExportAsFixedFormat($PdfPath, 17, $false, 0)
}
finally {
    if ($null -ne $document) {
        try { $document.Close($false) } catch { }
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document) } catch { }
    }
    if ($null -ne $word) {
        try { $word.Quit() } catch { }
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) } catch { }
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Get-Item -LiteralPath $DocxPath, $PdfPath | Select-Object FullName, Length, LastWriteTime
