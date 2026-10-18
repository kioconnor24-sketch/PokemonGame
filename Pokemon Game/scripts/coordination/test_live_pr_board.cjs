const fs=require('node:fs');
const assert=require('node:assert/strict');
const workflow=fs.readFileSync('.github/workflows/averon-agent-board.yml','utf8');
const script=workflow.split('          script: |\n')[1].split('      - uses: actions/upload-artifact')[0].split('\n').map(l=>l.startsWith('            ')?l.slice(12):l).join('\n');
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
const run=new AsyncFunction('github','context','core','require',script);
async function scenario(prs,checks,reviews){
 let summary='',written;const calls=[];
 const api={pulls:{list:Symbol('list'),listReviews:Symbol('reviews')},checks:{listForRef:Symbol('checks')},repos:{getBranch:async()=>({data:{commit:{sha:'base'}}})}};
 const github={rest:api,paginate:async(method,args)=>{calls.push(args);if(method===api.pulls.list)return prs;if(method===api.checks.listForRef)return checks;if(method===api.pulls.listReviews)return reviews;throw Error('unexpected API');}};
 const core={summary:{addRaw:s=>summary=s,write:async()=>{}}};
 await run(github,{repo:{owner:'o',repo:'r'}},core,name=>{assert.equal(name,'fs');return {writeFileSync:(p,c)=>written=JSON.parse(c)}});
 return {summary,written,calls};
}
(async()=>{
 const pr={number:1,html_url:'https://github.com/o/r/pull/1',draft:true,head:{sha:'head'},base:{sha:'base'},title:'${process.exit(99)}'};
 const a=await scenario([pr],[{id:1,app:{id:2},name:'guard',status:'completed',conclusion:'cancelled'},{id:2,app:{id:2},name:'guard',status:'completed',conclusion:'success'}],[{commit_id:'old',state:'APPROVED'},{commit_id:'head',state:'COMMENT'}]);
 assert.equal(a.written.pull_requests[0].checks.length,1);assert.equal(a.written.pull_requests[0].checks[0].conclusion,'success');
 assert.equal(a.written.pull_requests[0].current_head_reviews.length,1);assert.match(a.summary,/DRAFT/);assert.doesNotMatch(a.summary,/process.exit/);
 const b=await scenario([pr],[],[]);assert.match(b.summary,/checks UNKNOWN/);assert.equal(b.written.pull_requests[0].current_head_reviews.length,0);
 const c=await scenario([],[],[]);assert.equal(c.written.pull_requests.length,0);
 assert.doesNotMatch(workflow,/issues: write|pulls\.merge|issues\.update|actions\/checkout/);
 console.log('PASS: 6 board scenarios: latest rerun, exact-head reviews, draft, missing checks, empty queue, read-only/no PR execution');
})().catch(e=>{console.error(e);process.exitCode=1});

