const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const handlers={}, objects=new Map(), logs=[], chats=[];
let next=1;
function make(type,data,id='test-'+next++) {
  const p={...data,_type:type};
  if(p.pageid){p._pageid=p.pageid;delete p.pageid;}
  if(p.characterid){p._characterid=p.characterid;delete p.characterid;}
  const o={id,get(k,cb){if(cb)cb(p[k]);else return p[k];},set(changes){Object.assign(p,changes);},createCopy(changes){return make(type,{...p,...changes});}};
  objects.set(type+':'+id,o);return o;
}
const campaign=make('campaign',{playerpageid:'live',playerspecificpages:{}},'root');
campaign.sandboxVersion='1.5';
const context={state:{},on:(e,f)=>handlers[e]=f,log:s=>logs.push(s),sendChat:(...a)=>chats.push(a),Campaign:()=>campaign,
  getObj:(type,id)=>objects.get(type+':'+id),createObj:make,playerIsGM:id=>id==='gm',
  findObjs:q=>[...objects.values()].filter(o=>Object.entries(q).every(([k,v])=>o.get(k)===v)),
  getAttrByName:(id,n,k)=>[...objects.values()].find(o=>o.get('_type')==='attribute'&&o.get('_characterid')===id&&o.get('name')===n)?.get(k)};
vm.runInNewContext(fs.readFileSync(__dirname+'/GMControl.js','utf8'),context);handlers.ready();
make('page',{name:'Live',width:30,height:30},'live');
make('page',{name:'GM Framework Lab',width:25,height:25},'lab');
make('character',{name:'PC'},'pc');
const liveHP=make('attribute',{characterid:'pc',name:'hp',current:'33',max:'43'},'live-hp');
const live=make('graphic',{pageid:'live',name:'PC',represents:'pc',bar1_link:'live-hp',bar1_value:'33',bar1_max:'43',left:35,top:35,layer:'objects',statusmarkers:''},'live-token');
function cmd(q,player='gm') {handlers['chat:message']({type:'api',content:'!gmctl '+JSON.stringify(q),playerid:player});return JSON.parse(logs.at(-1).replace('GMCTL_RECEIPT ',''));}
const before=logs.length;
handlers['chat:message']({type:'api',content:'!gmctl {"op":"scene","page":"live"}',playerid:'player'});
assert.equal(logs.length,before,'Non-GM cannot inspect');
assert(cmd({op:'scene',page:'live'}).result.tokens.length===1);
assert.match(cmd({op:'edit',type:'graphic',id:'live-token',changes:{left:70},expect:{left:35},request:'bad-live'}).result.error,/Object not found/);
cmd({op:'lab',page:'lab'});
assert.match(cmd({op:'edit',type:'graphic',id:'live-token',changes:{left:70},expect:{left:35},request:'bad-live2'}).result.error,/Live token/);
const clone=cmd({op:'clone',id:'live-token',names:['hp'],request:'clone-1'}).result;
const id=clone.test.id,hp=clone.attributes.find(a=>a.name==='hp').id;
assert.equal(clone.test.bar1_link,'');assert.notEqual(clone.test.represents,'pc');assert.equal(clone.test.layer,'gmlayer');
const preview=cmd({op:'preview',type:'graphic',id,changes:{left:175,statusmarkers:'blue'},expect:{left:105,statusmarkers:''}});
assert.equal(preview.result.status,'PREVIEW');assert.equal(objects.get('graphic:'+id).get('left'),105);
cmd({op:'snapshot',label:'baseline',tokens:['live-token',id],attributes:['live-hp',hp]});
assert.match(cmd({op:'edit',type:'graphic',id,changes:{left:175},expect:{left:104},request:'stale'}).result.error,/Stale/);
assert.match(cmd({op:'edit',type:'graphic',id,changes:{represents:'pc'},expect:{represents:clone.character},request:'link'}).result.error,/not writable/);
assert.match(cmd({op:'edit',type:'graphic',id,changes:{left:999999},expect:{left:105},request:'outside'}).result.error,/outside/);
assert.equal(cmd({op:'edit',type:'graphic',id,changes:{left:175,statusmarkers:'blue',layer:'objects'},expect:{left:105,statusmarkers:'',layer:'gmlayer'},request:'move'}).result.status,'VERIFIED');
assert.equal(cmd({op:'compare',label:'baseline'}).result.changes.length,3);
assert.equal(cmd({op:'edit',type:'attribute',id:hp,changes:{current:'32'},expect:{current:'33'},request:'spend'}).result.status,'VERIFIED');
assert.equal(liveHP.get('current'),'33');assert.equal(live.get('left'),35);
assert.equal(cmd({op:'undo',transaction:'spend'}).result.status,'UNDONE');
objects.get('graphic:'+id).set({left:245});
assert.match(cmd({op:'undo',transaction:'move'}).result.error,/Undo conflict/);
objects.get('graphic:'+id).set({left:175});
assert.equal(cmd({op:'undo',transaction:'move'}).result.status,'UNDONE');
assert.equal(cmd({op:'compare',label:'baseline'}).result.unchanged,true);
assert.match(cmd({op:'edit',type:'graphic',id,changes:{left:175},expect:{left:105},request:'move'}).result.error,/already used/);
objects.get('graphic:'+id).set({bar1_link:'live-hp'});
assert.match(cmd({op:'edit',type:'graphic',id,changes:{bar1_value:'1'},expect:{bar1_value:'33'},request:'bar'}).result.error,/Linked bar/);
make('handout',{notes:'<script>bad</script> [[1d20]] @{PC|hp}'},'handout');
assert.equal(cmd({op:'source',type:'handout',id:'handout',field:'notes',limit:10}).result.next,10);
cmd({op:'source',type:'handout',id:'handout',field:'notes'});
assert(!chats.at(-1)[1].includes('<script>'));assert(!chats.at(-1)[1].includes('[['));assert(!chats.at(-1)[1].includes('@{'));
assert(chats.every(c=>c[1].startsWith('/w gm ')));
make('handout',{gmnotes:'x'.repeat(5000)},'long-handout');
cmd({op:'source',type:'handout',id:'long-handout',field:'gmnotes',limit:12000});
assert(chats.at(-1)[1].includes('page 1/'));
assert(chats.at(-1)[1].includes('more'));
assert(!chats.at(-1)[1].includes('\n'),'Long previews must not create a second, public chat line');
handlers['chat:message']({type:'api',content:'!gmctl {bad',playerid:'gm'});
assert(JSON.parse(logs.at(-1).replace('GMCTL_RECEIPT ','')).result.error);
campaign.set({playerpageid:'lab'});
assert.match(cmd({op:'clone',id:'live-token',request:'clone-bad'}).result.error,/player page/);
console.log('PASS: GM access, inspection, private escaped receipts, isolated clone, no live writes, preview, stale guards, field/bounds/link validation, resource edit, conflict-aware undo, snapshots, duplicate request rejection, malformed input, player-page isolation.');

// 1.1 reads: precise selection, deterministic pagination, complete transport, cache hints.
make('graphic',{pageid:'live',name:'Art',layer:'map'},'map-art');
let scene=cmd({op:'scene',page:'live',layers:['objects'],fields:['name','left']}).result;
assert.equal(scene.total,1);assert.equal(scene.tokens[0].left,35);
assert.equal(scene.tokens[0].bar1_value,undefined);assert.deepEqual(scene.characters,{});
assert.equal(cmd({op:'scene',page:'live',limit:1}).result.next,1);
assert.equal(cmd({op:'scene',page:'live',offset:1,limit:1}).result.next,null);
assert.match(cmd({op:'scene',page:'live',ids:[id]}).result.error,/not on requested page/);
assert.match(cmd({op:'token',id:'live-token',fields:['gmnotes']}).result.error,/Unsupported/);
const exact=cmd({op:'character',id:'pc',names:['hp','hp_temp']}).result;
assert.equal(exact.attributes.rows.length,1);assert.equal(exact.defaults[0].name,'hp_temp');
make('handout',{notes:'<p>Hello &amp; goodbye</p><p>[[1d20]] @{PC|hp}</p>'},'text-handout');
const raw=cmd({op:'source',type:'handout',id:'text-handout',field:'notes'}).result;
const plain=cmd({op:'source',type:'handout',id:'text-handout',field:'notes',view:'text'}).result;
assert.equal(raw.fingerprint,plain.fingerprint);assert(plain.text.includes('Hello & goodbye\n'));
assert(!chats.at(-1)[1].includes('[[1d20]]'));
assert.equal(cmd({op:'source',type:'handout',id:'text-handout',field:'notes',ifFingerprint:raw.fingerprint}).result.text,undefined);
objects.get('handout:text-handout').set({notes:'changed'});
assert.equal(cmd({op:'source',type:'handout',id:'text-handout',field:'notes',ifFingerprint:raw.fingerprint}).result.unchanged,false);
assert.match(cmd({op:'source',type:'handout',id:'text-handout',field:'notes',offset:-1}).result.error,/Invalid/);
assert.match(cmd({op:'source',type:'handout',id:'text-handout',field:'notes',offset:100}).result.error,/exceeds/);
const allText='First\n'+'x'.repeat(2600)+'\n[[1d20]] END';
make('handout',{notes:allText},'paged');
cmd({op:'source',type:'handout',id:'paged',field:'notes',limit:12000});
const firstChat=chats.at(-1)[1],receipt=firstChat.match(/Receipt ([a-z0-9-]+)/)[1];
assert(firstChat.includes('page 1/2'));
cmd({op:'more',receipt,page:1});assert(chats.at(-1)[1].includes('END OF RECEIPT'));assert(chats.at(-1)[1].includes('END'));
const batch=cmd({op:'batch',reads:[{op:'token',id:'missing'},{op:'source',type:'handout',id:'paged',field:'notes',limit:5},{op:'token',id:'live-token',fields:['left']}]}).result;
assert(batch.results[0].result.error);assert.equal(batch.results[1].result.text,'First');assert.equal(batch.results[2].result.left,35);
assert.match(cmd({op:'batch',reads:[{op:'edit'}]}).result.error,/only inspection/);
assert.match(cmd({op:'batch',reads:[{op:'batch'}]}).result.error,/only inspection/);

// Music is the only live mutation extension. Previews, stale guards, no timed advancement.
const a=make('jukeboxtrack',{title:'Quiet',playing:true,softstop:false,loop:true,volume:55},'music-a');
const b=make('jukeboxtrack',{title:'Companionship',playing:false,softstop:false,loop:false,volume:30},'music-b');
assert.match(cmd({op:'music',action:'define',cue:'quiet',tracks:['music-a'],volume:'55',request:'bad-vol'}).result.error,/integer/);
assert.equal(cmd({op:'music',action:'define',cue:'quiet',tracks:['music-b','music-a'],volume:45,request:'define-quiet'}).result.playbackChanged,false);
assert(a.get('playing'));assert(!b.get('playing'));
let previewMusic=cmd({op:'music',action:'start',cue:'quiet',preview:true}).result;
assert.equal(previewMusic.status,'PREVIEW');assert(a.get('loop'));
assert.match(cmd({op:'music',action:'start',cue:'quiet',request:'no-ui',expect:previewMusic.plan.expect}).result.error,/native playlist/);
a.set({volume:50});
assert.match(cmd({op:'music',action:'start',cue:'quiet',request:'stale-music',exclusiveReady:true,expect:previewMusic.plan.expect}).result.error,/Stale/);
function musicAction(action,request,extra={}) {return cmd({op:'music',action,request,exclusiveReady:true,expect:cmd({op:'music-status'}).result.fingerprint,...extra}).result;}
assert.equal(musicAction('start','start-quiet',{cue:'quiet'}).status,'VERIFIED_OBJECTS');
assert(!a.get('playing'));assert(b.get('playing'));assert.equal(b.get('volume'),45);assert(!b.get('loop'));
assert.match(musicAction('start','start-quiet',{cue:'quiet'}).error,/unique/);
cmd({op:'music',action:'define',cue:'quiet',tracks:['music-b'],volume:10,replace:true,request:'redefine'});
assert.equal(musicAction('next','next-quiet').status,'VERIFIED_OBJECTS');assert(a.get('playing'));assert.equal(a.get('volume'),45);
assert.match(musicAction('next','end-quiet').error,/End of cue/);
assert.equal(musicAction('stop','stop-quiet').status,'VERIFIED_OBJECTS');assert(!a.get('playing'));assert(!b.get('playing'));
const allObjectsBeforeRestart=JSON.stringify([...objects.values()].map(o=>[o.id,o.get('playing'),o.get('left'),o.get('current')]));
vm.runInNewContext(fs.readFileSync(__dirname+'/GMControl.js','utf8'),context);handlers.ready();
assert.equal(cmd({op:'music-status'}).result.cues.quiet.tracks[0],'music-b');
assert.equal(JSON.stringify([...objects.values()].map(o=>[o.id,o.get('playing'),o.get('left'),o.get('current')])),allObjectsBeforeRestart);
const nonGMLogs=logs.length;handlers['chat:message']({type:'api',content:'!gmctl {"op":"music","action":"stop"}',playerid:'player'});assert.equal(logs.length,nonGMLogs);
// A failed mid-cue write is recorded and never blindly reissued or called atomic.
a.set({playing:true});const originalSet=b.set;b.set=()=>{throw new Error('Injected track failure');};
assert.equal(musicAction('start','failure-cue',{cue:'quiet'}).status,'PARTIAL_FAILURE');
assert.equal(cmd({op:'music-status'}).result.active,null);
b.set=originalSet;
assert.equal(liveHP.get('current'),'33');assert.equal(live.get('left'),35);
assert(chats.every(c=>c[1].startsWith('/w gm ')&&!c[1].includes('\n')));
const originalFind=context.findObjs;
context.findObjs=q=>{const rows=originalFind(q);return q._type==='jukeboxtrack'?rows.concat(rows):rows;};
assert.equal(cmd({op:'list',type:'jukeboxtrack'}).result.total,2,'Deduplicate actual repeated jukebox IDs');
a.set({playing:true});assert.equal(cmd({op:'music-status'}).result.playing.length,1);
console.log('PASS 1.1: selected reads, scene pagination, exact attributes/defaults, text/raw source views, cache changes, full private receipt pagination, read-only batch isolation, manual music previews/expected-state guards, distinct nonlooping sequence, no startup playback, preserved definitions, duplicate/partial failure handling, no live game-state writes.');
