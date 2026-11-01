import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import sharp from 'sharp';
const dir=path.dirname(fileURLToPath(import.meta.url));
const base=path.resolve(dir,'../../outputs');
for(const f of await fs.readdir(path.join(base,'问卷分析/图表'))){
 if(f.endsWith('.svg'))await sharp(path.join(base,'问卷分析/图表',f),{density:200}).png().toFile(path.join(base,'问卷分析/图表',f.replace('.svg','.png')));
}
await sharp(path.join(base,'亲和图/亲和图_数字分组草案.svg'),{density:144}).png().toFile(path.join(base,'亲和图/亲和图_数字分组草案.png'));
await sharp(path.join(base,'亲和图/亲和图_数字分组草案.png')).resize({width:1860}).toFile(path.join(dir,'affinity-overview.png'));
console.log('Rasterized 11 charts and affinity diagram.');
