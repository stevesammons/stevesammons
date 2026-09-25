// usage: node mapshot.js file.html outprefix [chapterCount]
const {chromium}=require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright');
(async()=>{const [,,file,out]=process.argv;const b=await chromium.launch();
for(const [w,n] of [[1000,'d'],[390,'m']]){const p=await b.newPage({viewport:{width:w,height:1100},deviceScaleFactor:1});const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
 await p.goto('file://'+file);await p.waitForTimeout(1800);
 const tabs=await p.$$('.bm-tab');
 await p.screenshot({path:`${out}-${n}1.png`,fullPage:true});
 if(tabs.length>1){await tabs[1].click();await p.waitForTimeout(1600);await p.screenshot({path:`${out}-${n}2.png`,fullPage:true});}
 const sw=await p.evaluate(()=>document.documentElement.scrollWidth);
 console.log(n,'tabs',tabs.length,'scrollW',sw,'errors',errs.slice(0,3));await p.close();}
await b.close();})();
