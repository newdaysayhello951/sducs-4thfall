import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const dir=path.dirname(fileURLToPath(import.meta.url));
const data=JSON.parse(await fs.readFile(path.join(dir,'analysis.json'),'utf8'));
const out=path.resolve(dir,'../../outputs/问卷分析');
const wb=Workbook.create();
const result=wb.worksheets.add('统计结果');
const raw=wb.worksheets.add('原始答卷');
const dict=wb.worksheets.add('题目说明');
const multi=wb.worksheets.add('多选展开');
const col=i=>{let s='';for(i++;i;i=Math.floor((i-1)/26))s=String.fromCharCode(65+(i-1)%26)+s;return s;};
function base(s,range){s.showGridLines=false;s.getRange(range).format.font={name:'Microsoft YaHei',size:11};s.getRange(range).format.rowHeight=26;s.getRange(range).format.verticalAlignment='center';}
function header(s,r){s.getRange(r).format.fill='#243C58';s.getRange(r).format.font={name:'Microsoft YaHei',size:11,bold:true,color:'#FFFFFF'};s.getRange(r).format.rowHeight=30;}
const selections=data.records.flatMap(r=>['Q10','Q20','Q21'].flatMap(q=>r[q].split('；').map(option=>[r['编号'],q,option])));
base(multi,`A1:C${selections.length+1}`);
multi.getRange('A1:C1').values=[['答卷编号','题号','所选项']];
multi.getRange(`A2:C${selections.length+1}`).values=selections;
multi.getRange(`A1:B${selections.length+1}`).format.columnWidth=14;multi.getRange(`C1:C${selections.length+1}`).format.columnWidth=68;
header(multi,'A1:C1');multi.freezePanes.freezeRows(1);
base(raw,'A1:AE15');
raw.getRange('A1:AE1').values=[data.headers];
const vals=data.records.map(r=>data.headers.map(k=>k==='提交时间 UTC'?new Date(r[k].replace(' ','T')+'Z'):r[k]));
raw.getRange('A2:AE12').values=vals;
raw.getRange('A1:AE12').format.columnWidth=23;
raw.getRange('A1:A12').format.columnWidth=10;
raw.getRange('E1:E12').format.columnWidth=30;
raw.getRange('E2:E12').setNumberFormat('yyyy-mm-dd hh:mm:ss');
raw.getRange('P1:T12').format.columnWidth=12;
raw.getRange('F2:AE12').format.wrapText=true;
raw.getRange('A2:AE12').format.rowHeight=180;
raw.getRange('O1:O12').format.columnWidth=47;
raw.getRange('AC1:AE12').format.columnWidth=48;
header(raw,'A1:AE1');raw.freezePanes.freezeRows(1);raw.freezePanes.freezeColumns(1);
raw.getRange('A14').values=[['来源：'+data.source+'，问卷原始数据工作表。按编号保留全部Q1—Q22回答及参与资格；空白保持为空白。']];
raw.getRange('A15').values=[['日期单元格展示UTC时间至秒；毫秒精度以原始文件为准。原始文件未修改。']];
base(dict,'A1:D33');
dict.getRange('A1:D1').values=[['题号','题型','完整题目','完整选项与说明']];
dict.getRange(`A2:D${Object.keys(data.definitions).length+1}`).values=Object.entries(data.definitions).map(([q,d])=>[q,d.type,d.title,d.options.join('\n')]);
dict.getRange('A1:A33').format.columnWidth=10;dict.getRange('B1:B33').format.columnWidth=22;dict.getRange('C1:C33').format.columnWidth=62;dict.getRange('D1:D33').format.columnWidth=74;
dict.getRange('A2:D23').format.wrapText=true;dict.getRange('A2:D23').format.verticalAlignment='top';
for(let i=0;i<22;i++)dict.getRange(`A${i+2}:D${i+2}`).format.rowHeight=Math.max(90,Object.values(data.definitions)[i].options.length*21+12);
header(dict,'A1:D1');dict.freezePanes.freezeRows(1);
base(result,'A1:G220');
result.getRange('A1:A220').format.columnWidth=13;result.getRange('B1:B220').format.columnWidth=56;
result.getRange('C1:F220').format.columnWidth=15;result.getRange('G1:G220').format.columnWidth=26;
result.getRange('A2').values=[['SmartCampus+ 问卷统计']];result.getRange('A2').format.font={size:17,bold:true};
result.getRange('A4:B4').values=[['有效答卷',null]];result.getRange('B4').formulas=[["=COUNTA('原始答卷'!$A$2:$A$12)"]];
result.getRange('A6').values=[['Q11 功能排序：计分为5减名次；均值越小、得分越高，表示本样本相对更优先。']];
result.getRange('A7:G7').values=[['字段','功能','排序得分','平均名次','第一名人数','第五名人数','有效人数']];header(result,'A7:G7');
for(let i=0;i<data.rank.length;i++){
 const r=i+8,x=data.rank[i],c=col(data.headers.indexOf(x.field)),ref=`'原始答卷'!$${c}$2:$${c}$12`;
 result.getRange(`A${r}:G${r}`).values=[[x.field,x.label,null,null,null,null,null]];
 result.getRange(`C${r}:G${r}`).formulas=[[`=5*COUNT(${ref})-SUM(${ref})`,`=AVERAGE(${ref})`,`=COUNTIFS(${ref},1)`,`=COUNTIFS(${ref},5)`,`=COUNT(${ref})`]];
}
result.getRange('D8:D12').setNumberFormat('0.00');
const notes=[
 '方法：各题比例以有效作答人数为分母。多选题按选择人数计数，比例之和可超过100%。',
 '缺失：Q5缺R02，共10人有效；Q22仅R01与R05作答，共2人有效。不填补缺失。',
 '核对：11个唯一编号、无完整重复答卷；Q11排序完整且无重名次；Q20互斥规则和Q21最多三项均通过。',
 '一致性：与Word逐项核对286个回答，无内容差异；元数据时间不在此比较范围内。',
 '保留差异：R10在Q19接受连接课表，但Q20不愿共享课表；R09、R10不希望主动通知但给出非零容忍上限。',
 '解释：以上跨题差异不能仅凭现有数据判错，原样保留。小样本便利招募，采用描述统计，不作因果和总体推断。',
 '使用：本工作簿为本次分析版本；多选展开按原回答拆分。更改或新增原答卷后须重新生成多选展开、统计范围及PDF。'
];
notes.forEach((x,i)=>{const r=i+15;result.getRange(`A${r}:G${r}`).merge();result.getRange(`A${r}`).values=[[x]];result.getRange(`A${r}:G${r}`).format.wrapText=true;result.getRange(`A${r}:G${r}`).format.rowHeight=42;});
result.getRange('A23:G23').values=[['题号','选项','人数','有效人数','比例','缺失人数','题型']];header(result,'A23:G23');
const expected=[];
for(let i=0;i<data.stats.length;i++){
 const x=data.stats[i],r=24+i,c=col(data.headers.indexOf(x.q)),ref=`'原始答卷'!$${c}$2:$${c}$12`;
 result.getRange(`A${r}:G${r}`).values=[[x.q,x.option,null,null,null,null,x.type]];
 const countFormula=x.type==='多选题'?`=COUNTIFS('多选展开'!$B$2:$B$${selections.length+1},A${r},'多选展开'!$C$2:$C$${selections.length+1},B${r})`:`=COUNTIFS(${ref},B${r})`;
 result.getRange(`C${r}:F${r}`).formulas=[[countFormula,`=COUNTA(${ref})`,`=C${r}/D${r}`,`=$B$4-D${r}`]];
 result.getRange(`E${r}`).setNumberFormat('0.0%');
 expected.push([r,x]);
 if(i===0||data.stats[i-1].q!==x.q)result.getRange(`A${r}:G${r}`).format.borders={top:{style:'thin',color:'#B9C4D0'}};
}
let last=24+data.stats.length+2;
result.getRange(`A${last}:C${last}`).values=[['Q22','编号','开放回答原文']];header(result,`A${last}:C${last}`);
for(const r of data.records.filter(x=>x.Q22)){last++;result.getRange(`A${last}:C${last}`).values=[['Q22',r['编号'],r.Q22]];result.getRange(`C${last}:G${last}`).merge();result.getRange(`C${last}:G${last}`).format.wrapText=true;result.getRange(`A${last}:G${last}`).format.rowHeight=65;}
result.freezePanes.freezeRows(0);
wb.recalculate();
for(const [r,x] of expected){const got=result.getRange(`C${r}:F${r}`).values[0];if(Math.abs(got[0]-x.count)>1e-8||got[1]!==x.valid||Math.abs(got[2]-x.pct)>1e-8||got[3]!==x.missing)throw Error(`Mismatch ${x.q} ${x.option}: ${JSON.stringify(got)}`);}
for(let i=0;i<5;i++){const actual=result.getRange(`C${i+8}:G${i+8}`).values[0],x=data.rank[i];if(actual[0]!==x.score||Math.abs(actual[1]-x.mean)>1e-8||actual[2]!==x.first||actual[3]!==x.last||actual[4]!==11)throw Error('Rank mismatch');}
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!',options:{useRegex:true,maxResults:10},summary:'公式错误检查'})).ndjson);
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(out,'SmartCampus_问卷整理与统计.xlsx'));
for(const [name,range,file] of [['统计结果','A2:G12','summary'],['统计结果','A23:G37','counts'],['原始答卷','A1:H3','raw'],['题目说明','A1:D4','dictionary'],['多选展开','A1:C9','multi']]){
 try{const b=await wb.render({sheetName:name,range,scale:1,format:'png'});await fs.writeFile(path.join(dir,file+'.png'),new Uint8Array(await b.arrayBuffer()));}catch(e){console.log('RENDER_ERROR',name,String(e).slice(0,400));}
}
console.log('Exported and independently verified '+expected.length+' option statistics and 5 rankings.');
