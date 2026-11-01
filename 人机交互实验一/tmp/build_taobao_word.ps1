$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$outDir = Join-Path (Get-Location) 'output/docx'
[System.IO.Directory]::CreateDirectory($outDir) | Out-Null
$docPath = Join-Path $outDir '淘宝可用性测试报告_简洁版.docx'
$parts = [System.Collections.Generic.List[string]]::new()
function Para([string]$content, [string]$style = 'Normal') {
    $escaped = [System.Security.SecurityElement]::Escape($content)
    $parts.Add('<w:p><w:pPr><w:pStyle w:val="' + $style + '"/></w:pPr><w:r><w:t xml:space="preserve">' + $escaped + '</w:t></w:r></w:p>')
}
Para '淘宝 App 快速可用性测试报告' 'Title'
Para '姓名1：________  学号1：________    姓名2：________  学号2：________' 'Meta'
Para '实验日期：________    测试设备及淘宝版本：________________' 'Meta'
Para '说明：以下为模拟案例，操作记录与耗时请根据实际测试修改，图片在标注处补充。' 'Note'
Para '实验对象与方法' 'Heading1'
Para '选择手机端淘宝 App，测试“搜索筛选商品”和“收藏后重新查找”两个典型用途。任务一由同学1操作、同学2记录；任务二交换角色。观察者记录操作步骤、遇到的问题、新用户可能不懂的操作及完成效率。'
Para '任务一：搜索并筛选商品' 'Heading1'
Para '任务目标：找到一款价格在50～100元、容量约500mL的保温杯，确认所选规格对应的价格。'
Para '操作过程：打开淘宝，搜索“500mL保温杯”；找到筛选入口，设置价格范围；进入候选商品详情页，查看容量和价格；选择500mL规格，确认价格为89元，完成任务。'
Para '遇到的问题：搜索结果显示“59元起”，操作者最初以为这是500mL的价格，进入规格页面后才发现59元对应350mL，需要重新核对。'
Para '新用户可能不懂的操作：不知道如何设置价格筛选，也可能不清楚“起价”与不同商品规格之间的关系。'
Para '效率：模拟耗时2分18秒，回退1次，无需帮助即可完成。搜索较顺利，主要时间花在查找筛选入口和核对规格价格。'
Para '【图片1插入位置：商品搜索结果及价格筛选截图】' 'Placeholder'
Para '【图片2插入位置：商品规格页面截图，展示500mL及对应价格】' 'Placeholder'
$parts.Add('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
Para '任务二：收藏商品并重新查找' 'Heading1'
Para '人员分工：同学2操作，同学1记录，与任务一交换角色。'
Para '任务目标：收藏两款感兴趣的保温杯，返回淘宝首页，再找到这两款已收藏的商品。'
Para '操作过程：搜索保温杯，依次打开两款商品并点击收藏；返回首页后，先进入购物车查找，未找到后返回；进入个人页面，在观察者提示后找到商品收藏入口，打开并确认两款商品。'
Para '遇到的问题：操作者不确定第一次收藏是否成功，重复点击导致取消，之后再次收藏；返回首页后，将收藏商品与加入购物车混淆，走了多余的步骤。'
Para '新用户可能不懂的操作：不清楚收藏与购物车的区别，也不知道收藏的商品需要从哪里重新进入。'
Para '效率：模拟耗时3分06秒，回退2次，求助1次，提示后完成。主要时间花在确认收藏状态和寻找收藏入口。'
Para '【图片3插入位置：商品详情页截图，标出收藏按钮及收藏状态】' 'Placeholder'
Para '【图片4插入位置：商品收藏列表截图，展示两款已收藏商品】' 'Placeholder'
Para '产品目标与价值' 'Heading1'
Para '淘宝的目标是帮助用户发现、比较和购买商品。搜索与筛选使用户能够缩小选择范围，找到符合预算和需求的商品；收藏帮助用户保存候选商品，便于以后查找和比较，减少重复搜索。'
Para '测试小结' 'Heading1'
Para '本模拟案例中，两项任务均可完成，但规格价格的表达、收藏反馈和收藏入口给操作带来额外成本。可改进的方向是明确展示规格对应价格、强化收藏成功提示，并让收藏入口更容易发现。'
Para '提交提醒：补全姓名、学号及实际记录，插入截图后导出为PDF；按“姓名1-学号1-姓名2-学号2-UsabilityTest.pdf”命名。原作业截止时间为9月17日24:00，提交方式由助教通知。' 'Note'
$document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + ($parts -join '') + '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708"/></w:sectPr></w:body></w:document>'
# compact_reference_guide; named overrides: Chinese fonts, compact black academic headings,
# plain memo masthead, and shaded text-only image placeholders. No tables or manual lists.
$styles = @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="宋体"/><w:sz w:val="22"/><w:lang w:val="en-US" w:eastAsia="zh-CN"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:before="0" w:after="120" w:line="300" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:pPr><w:widowControl/><w:spacing w:before="0" w:after="120" w:line="300" w:lineRule="auto"/></w:pPr><w:rPr><w:color w:val="000000"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:jc w:val="center"/><w:spacing w:before="0" w:after="200" w:line="300" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:eastAsia="黑体"/><w:b/><w:sz w:val="36"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:keepLines/><w:outlineLvl w:val="0"/><w:spacing w:before="180" w:after="100" w:line="300" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:eastAsia="黑体"/><w:b/><w:sz w:val="26"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Meta"><w:name w:val="Metadata"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="0" w:after="100" w:line="300" w:lineRule="auto"/></w:pPr><w:rPr><w:sz w:val="20"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Note"><w:name w:val="Note"/><w:basedOn w:val="Normal"/><w:rPr><w:sz w:val="18"/><w:color w:val="666666"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Placeholder"><w:name w:val="Image Placeholder"/><w:basedOn w:val="Normal"/><w:pPr><w:keepLines/><w:spacing w:before="100" w:after="120" w:line="300" w:lineRule="auto"/><w:shd w:val="clear" w:fill="F2F4F7"/></w:pPr><w:rPr><w:color w:val="666666"/><w:sz w:val="20"/></w:rPr></w:style>
</w:styles>
'@
$files = @{
 '[Content_Types].xml' = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'
 '_rels/.rels' = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
 'word/document.xml' = $document
 'word/styles.xml' = $styles
 'word/_rels/document.xml.rels' = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'
}
$stream = [System.IO.File]::Open($docPath, [System.IO.FileMode]::Create)
$zip = [System.IO.Compression.ZipArchive]::new($stream,[System.IO.Compression.ZipArchiveMode]::Create)
foreach ($name in $files.Keys) {
    [xml]$valid = $files[$name]
    $entry = $zip.CreateEntry($name)
    $writer = [System.IO.StreamWriter]::new($entry.Open(),[System.Text.UTF8Encoding]::new($false))
    $writer.Write($files[$name]); $writer.Dispose()
}
$zip.Dispose(); $stream.Dispose()
$check = [System.IO.Compression.ZipFile]::OpenRead($docPath)
if ($check.Entries.Count -ne 5) { throw 'Package structure check failed' }
$check.Dispose()
Write-Output $docPath
Write-Output 'OOXML structure verified; four editable image placeholders included.'
