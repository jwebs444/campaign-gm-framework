/* GM Control 1.1.0 — stages 1/2: GM inspection and isolated test edits.
 * No timers, rolls, automatic resource expenditure or HTTP. Live music cues only; game-state edits remain test-only.
 * Commands: !gmctl {"op":"help","request":"unique-label"}
 */
(function () {
  'use strict';
  var VERSION = '1.1.0';
  var KEY = 'GMControl';
  var TOKEN = ['name','_pageid','represents','layer','left','top','width','height','rotation','statusmarkers',
    'bar1_link','bar1_value','bar1_max','bar2_link','bar2_value','bar2_max','bar3_link','bar3_value','bar3_max',
    'bar4_link','bar4_value','bar4_max','controlledby','showplayers_name','showplayers_bar1','showplayers_bar2','showplayers_bar3'];
  var PAGE = ['name','width','height','snapping_increment','grid_type','grid_offset_x','grid_offset_y','scale_number','scale_units','archived'];
  var RESOURCE = []; // Configure names for your sheet, or use explicit names/all/filter on reads.
  function db() { return state[KEY]; }
  function own(o,k) { return Object.prototype.hasOwnProperty.call(o,k); }
  function assert(ok,why) { if (!ok) throw new Error(why); }
  function obj(type,id) { var o=getObj(type,id); assert(o,'Object not found: '+type+' '+id); return o; }
  function findUnique(query) {
    // Live sandbox may repeat a jukebox object referenced by multiple playlists.
    var seen={};return findObjs(query).filter(function(o){if(own(seen,o.id))return false;seen[o.id]=true;return true;});
  }
  function read(o,fields) { var r={id:o.id}; fields.forEach(function(k){ var v=o.get(k); r[k]=v===undefined?null:v; }); return r; }
  function values(o,fields) { var r={}; fields.forEach(function(k){ var v=o.get(k); r[k]=v===undefined?null:v; }); return r; }
  function eq(a,b) { return JSON.stringify(a)===JSON.stringify(b); }
  function escape(s) { return String(s).replace(/[&<>"'\[\]{}@]/g,function(c){return '&#'+c.charCodeAt(0)+';';}); }
  // Volatile presentation cache only. Never persists source prose into campaign state.
  var receipts=[], receiptSerial=0, receiptSession=Date.now().toString(36);
  function display(entry,page) {
    assert(Number.isInteger(page)&&page>=0&&page<entry.pages.length,'Invalid receipt page');
    var more=page+1<entry.pages.length?'!gmctl '+JSON.stringify({op:'more',receipt:entry.id,page:page+1}):'END OF RECEIPT';
    sendChat('GM Control','/w gm <div><b>GM Control '+VERSION+' | '+escape(entry.label)+'</b><br>'+
      'Receipt '+entry.id+' · page '+(page+1)+'/'+entry.pages.length+'<pre style="white-space:pre-wrap">'+
      escape(entry.pages[page]).replace(/\r?\n/g,'<br>')+'</pre><small>'+escape(more)+'</small></div>',null,{noarchive:true});
  }
  function reply(q,result) {
    var r={version:VERSION,request:q.request||null,op:q.op,at:new Date().toISOString(),result:result};
    log('GMCTL_RECEIPT '+JSON.stringify(r));
    var body;
    if(q.op==='source'&&own(result,'text')) {
      var meta=Object.assign({},result);delete meta.text;
      body=JSON.stringify(meta,null,2)+'\n\n'+result.text;
    } else body=JSON.stringify(result,null,2);
    // Every character remains available. Split without consuming a newline or surrogate pair.
    var pages=[];
    while(body.length) {
      var end=Math.min(2400,body.length);
      if(end<body.length&&/[\uD800-\uDBFF]/.test(body.charAt(end-1)))end--;
      pages.push(body.slice(0,end));body=body.slice(end);
    }
    var entry={id:receiptSession+'-'+(++receiptSerial),label:q.request||q.op,pages:pages.length?pages:['(empty)']};
    receipts.push(entry);if(receipts.length>12)receipts.shift();
    display(entry,0);
  }
  function fields(q,allowedFields,defaults) {
    if(q.fields===undefined)return defaults;
    assert(Array.isArray(q.fields)&&q.fields.length>0&&q.fields.length<=allowedFields.length,'Invalid fields');
    assert(q.fields.every(function(k){return allowedFields.indexOf(k)>=0;}),'Unsupported read field');
    return q.fields;
  }
  function fingerprint(text) {
    // Non-cryptographic cache hint; exact source remains the authority.
    var h=2166136261;
    for(var i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619);}
    return text.length+':'+(h>>>0).toString(16);
  }
  function plainSource(raw) {
    return raw.replace(/<br\s*\/?\s*>/gi,'\n').replace(/<\/(p|div|li|h[1-6]|tr)>/gi,'\n')
      .replace(/<[^>]*>/g,'').replace(/&(amp|lt|gt|quot|apos|nbsp);/g,function(_,n){return {amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",nbsp:' '}[n];})
      .replace(/&#(x[0-9a-f]+|[0-9]+);/gi,function(m,n){var v=n[0].toLowerCase()==='x'?parseInt(n.slice(1),16):parseInt(n,10);return v<=0x10ffff?String.fromCodePoint(v):m;});
  }
  function pageRows(q,rows) {
    var offset=q.offset===undefined?0:q.offset, limit=q.limit===undefined?40:q.limit;
    assert(Number.isInteger(offset)&&offset>=0,'Invalid offset');
    assert(Number.isInteger(limit)&&limit>0&&limit<=100,'Limit must be 1–100');
    return {total:rows.length,offset:offset,next:offset+limit<rows.length?offset+limit:null,rows:rows.slice(offset,offset+limit)};
  }
  function attrs(id) { return findUnique({_type:'attribute',_characterid:id}); }
  function character(id,q) {
    var c=obj('character',id), aa=attrs(id);
    if(q.names!==undefined)assert(Array.isArray(q.names)&&q.names.length>0&&q.names.length<=30&&q.names.every(function(n){return typeof n==='string';}),'Invalid attribute names');
    var selected=aa.filter(function(a){return q.all || (q.names?q.names.indexOf(a.get('name'))>=0:(q.filter?String(a.get('name')).toLowerCase().indexOf(q.filter.toLowerCase())>=0:RESOURCE.indexOf(a.get('name'))>=0));});
    selected.sort(function(a,b){return String(a.get('name')).localeCompare(String(b.get('name')));});
    return {character:read(c,['name','archived','controlledby','inplayerjournals']),attributes:pageRows(q,selected.map(function(a){return read(a,['name','current','max']);})),
      defaults:q.all||q.filter?null:(q.names||RESOURCE).filter(function(n){return !aa.some(function(a){return a.get('name')===n;});}).map(function(n){
        return {name:n,current:getAttrByName(id,n,'current'),max:getAttrByName(id,n,'max'),note:'No stored attribute; default/formula is not a verified resource interpretation'};
      })};
  }
  function labPage() {
    var p=obj('page',db().lab);
    assert(p.get('name')==='GM Framework Lab','Lab page was renamed; editing blocked');
    assert(Campaign().get('playerpageid')!==p.id,'Lab is the player page; editing blocked');
    var split=Campaign().get('playerspecificpages')||{};
    if(typeof split==='string') { try {split=JSON.parse(split);} catch(e) {throw new Error('Cannot verify player page assignments');} }
    assert(!Object.keys(split).some(function(k){return split[k]===p.id;}),'Player assigned to lab; editing blocked');
    return p;
  }
  function allowed(type,id) {
    labPage();
    var o=obj(type,id);
    if(type==='graphic') {
      assert(db().testTokens.indexOf(id)>=0,'Live token editing is disabled in stages 1/2');
      assert(o.get('_pageid')===db().lab,'Test token moved outside lab');
      assert(!o.get('represents')||db().testCharacters.indexOf(o.get('represents'))>=0,'Test token linked to live character');
      [1,2,3,4].forEach(function(n){assert(!o.get('bar'+n+'_link'),'Linked bar edits are disabled');});
    } else {
      assert(type==='attribute'&&db().testAttributes.indexOf(id)>=0,'Live attribute editing is disabled in stages 1/2');
      assert(db().testCharacters.indexOf(o.get('_characterid'))>=0,'Attribute belongs to a live character');
    }
    return o;
  }
  function validate(o,type,changes) {
    assert(changes&&typeof changes==='object'&&!Array.isArray(changes),'changes must be an object');
    var keys=Object.keys(changes); assert(keys.length>0&&keys.length<=12,'Invalid number of fields');
    var allowedKeys=type==='graphic'?['left','top','rotation','layer','statusmarkers','bar1_value','bar1_max','bar2_value','bar2_max','bar3_value','bar3_max']:['current','max'];
    keys.forEach(function(k){
      assert(allowedKeys.indexOf(k)>=0,'Field not writable: '+k);
      var v=changes[k];
      if(['left','top','rotation'].indexOf(k)>=0) {
        assert(typeof v==='number'&&Number.isFinite(v),'Expected finite coordinate/rotation');
        if(k!=='rotation') { var p=obj('page',o.get('_pageid')); assert(v>=0&&v<=70*Number(p.get(k==='left'?'width':'height')),'Coordinate outside page'); }
        else assert(v>=0&&v<360,'Rotation must be 0–359');
      } else if(k==='layer') assert(v==='gmlayer'||v==='objects','Only GM/token layers allowed');
      else if(k==='statusmarkers') assert(typeof v==='string'&&/^[a-zA-Z0-9_:@,\- ]{0,500}$/.test(v),'Invalid marker list');
      else assert((typeof v==='string'||typeof v==='number')&&/^(-?\d+(\.\d+)?)?$/.test(String(v)),'Resource edits require a number or empty string');
    });
    return keys;
  }
  function mutation(q) {
    var o=allowed(q.type,q.id), fields=validate(o,q.type,q.changes);
    assert(q.expect&&typeof q.expect==='object'&&!Array.isArray(q.expect),'Exact expected values required');
    assert(eq(Object.keys(q.expect).sort(),fields.slice().sort()),'expect must cover exactly the changed fields');
    var before=values(o,fields);
    assert(eq(before,valuesFrom(q.expect,fields)),'Stale expected values; inspect again');
    if(q.op==='preview') return reply(q,{status:'PREVIEW',type:q.type,id:q.id,before:before,requested:q.changes});
    assert(typeof q.request==='string'&&/^[a-zA-Z0-9_-]{1,80}$/.test(q.request),'Unique request label required');
    assert(!own(db().used,q.request),'Request already used; inspect its receipt, do not retry blindly');
    // Reserve before set, so even a partial failure cannot be blindly retried.
    db().used[q.request]=true;
    var tx={request:q.request,type:q.type,id:q.id,before:before,requested:q.changes,status:'STARTED'};
    db().transactions.push(tx); if(db().transactions.length>30) db().transactions.shift();
    o.set(q.changes);
    tx.after=values(o,fields); tx.status=eq(tx.after,valuesFrom(q.changes,fields))?'VERIFIED':'MISMATCH';
    reply(q,tx);
  }
  function valuesFrom(data,fields) {var out={}; fields.forEach(function(k){out[k]=data[k];});return out;}
  function capture(q) {
    assert(Array.isArray(q.tokens)&&q.tokens.length<=40,'tokens array required (maximum 40)');
    assert(Array.isArray(q.attributes||[])&&(q.attributes||[]).length<=100,'Invalid attributes');
    return {tokens:q.tokens.map(function(id){return read(obj('graphic',id),TOKEN);}),attributes:(q.attributes||[]).map(function(id){return read(obj('attribute',id),['_characterid','name','current','max']);})};
  }
  var TRACK=['title','playing','softstop','volume','loop'];
  var COMPACT=['name','represents','layer','left','top','statusmarkers','bar1_value','bar1_max'];
  var READS=['ping','list','token','character','scene','source','music-status'];
  function inspect(q,done) {
    if(q.op==='ping')return done({ready:true,mode:'READ_LIVE / EDIT_TEST_COPIES / MANUAL_MUSIC',lab:db().lab});
    if(q.op==='music-status')return done(musicStatus());
    if(q.op==='list') {
      assert(['page','character','handout','jukeboxtrack'].indexOf(q.type)>=0,'Unsupported list type');
      var ff=q.type==='page'?PAGE:q.type==='jukeboxtrack'?TRACK:['name','archived'];
      var rows=findUnique({_type:q.type}).map(function(o){return read(o,ff);}).filter(function(r){return !q.filter||String(r.name||r.title).toLowerCase().indexOf(q.filter.toLowerCase())>=0;});
      rows.sort(function(a,b){return String(a.name||a.title).localeCompare(String(b.name||b.title))||a.id.localeCompare(b.id);});
      return done(pageRows(q,rows));
    }
    if(q.op==='token')return done(read(obj('graphic',q.id),fields(q,TOKEN,TOKEN)));
    if(q.op==='character')return done(character(q.id,q));
    if(q.op==='scene') {
      var p=obj('page',q.page), tokens=findUnique({_type:'graphic',_pageid:p.id});
      if(q.ids!==undefined) {
        assert(Array.isArray(q.ids)&&q.ids.length<=40,'Invalid token IDs');
        q.ids.forEach(function(id){assert(obj('graphic',id).get('_pageid')===p.id,'Selected token not on requested page');});
        tokens=tokens.filter(function(t){return q.ids.indexOf(t.id)>=0;});
      }
      if(q.layers!==undefined){assert(Array.isArray(q.layers)&&q.layers.length>0&&q.layers.every(function(l){return ['map','objects','gmlayer','walls','foreground'].indexOf(l)>=0;}),'Invalid layers');tokens=tokens.filter(function(t){return q.layers.indexOf(t.get('layer'))>=0;});}
      tokens.sort(function(a,b){return a.id.localeCompare(b.id);});
      var selected=pageRows(q,tokens), chars={};
      if(q.characters===true)selected.rows.forEach(function(t){var id=t.get('represents');if(id&&!own(chars,id))chars[id]=character(id,{names:q.names,limit:100});});
      return done({page:read(p,PAGE),total:selected.total,offset:selected.offset,next:selected.next,
        tokens:selected.rows.map(function(t){return read(t,fields(q,TOKEN,q.compact===false?TOKEN:COMPACT));}),characters:chars,
        note:'Only requested page slice. Character resources opt-in. Pixel centers; local canon controls fiction.'});
    }
    if(q.op==='source') {
      assert((q.type==='handout'&&['notes','gmnotes'].indexOf(q.field)>=0)||(q.type==='character'&&['bio','gmnotes'].indexOf(q.field)>=0),'Unsupported source field');
      var offset=q.offset===undefined?0:q.offset,limit=q.limit===undefined?2000:q.limit;
      assert(Number.isInteger(offset)&&offset>=0&&Number.isInteger(limit)&&limit>0&&limit<=12000,'Invalid source slice');
      assert(q.view===undefined||q.view==='raw'||q.view==='text','view must be raw or text');
      return obj(q.type,q.id).get(q.field,function(raw){try{
        raw=String(raw||'');var signature=fingerprint(raw),view=q.view||'raw',body=view==='text'?plainSource(raw):raw;
        assert(offset<=body.length,'Offset exceeds source length');
        var result={id:q.id,field:q.field,view:view,fingerprint:signature,rawLength:raw.length,total:body.length,offset:offset,
          next:offset+limit<body.length?offset+limit:null,unchanged:q.ifFingerprint===signature};
        if(!result.unchanged)result.text=body.slice(offset,offset+limit);
        done(result);
      }catch(e){done({error:e.message});}});
    }
    throw new Error('Unsupported read operation');
  }
  function musicStatus() {
    var rows=findUnique({_type:'jukeboxtrack'}).map(function(o){return read(o,TRACK);});
    rows.sort(function(a,b){return a.id.localeCompare(b.id);});
    return {fingerprint:fingerprint(JSON.stringify(rows)),playing:rows.filter(function(r){return r.playing;}),active:db().music.active,cues:db().music.cues,
      note:'Object flags only, not audible playback. Native playlists must be stopped through UI before Mod cue control.'};
  }
  function fresh(q) {
    assert(typeof q.request==='string'&&/^[a-zA-Z0-9_-]{1,80}$/.test(q.request)&&!own(db().used,q.request),'Fresh unique request label required');
    db().used[q.request]=true;
  }
  function music(q) {
    if(q.action==='define') {
      assert(typeof q.cue==='string'&&/^[a-zA-Z0-9_-]{1,60}$/.test(q.cue),'Invalid cue name');
      assert(!own(db().music.cues,q.cue)||q.replace===true,'Cue exists; explicit replace required');
      assert(own(db().music.cues,q.cue)||Object.keys(db().music.cues).length<12,'Maximum 12 cues');
      assert(Array.isArray(q.tracks)&&q.tracks.length>0&&q.tracks.length<=12&&new Set(q.tracks).size===q.tracks.length,'Cue requires 1–12 distinct track IDs');
      q.tracks.forEach(function(id){obj('jukeboxtrack',id);});
      assert(Number.isInteger(q.volume)&&q.volume>=0&&q.volume<=100,'Volume must be integer 0–100');
      fresh(q);db().music.cues[q.cue]={tracks:q.tracks.slice(),volume:q.volume};
      return reply(q,{status:'DEFINED',cue:q.cue,value:db().music.cues[q.cue],playbackChanged:false});
    }
    assert(['start','next','stop'].indexOf(q.action)>=0,'Music action must be define/start/next/stop');
    var now=musicStatus(),active=db().music.active, cue=null,index=0,target=null;
    if(q.action!=='stop') {
      var name=q.action==='start'?q.cue:active&&active.cue;
      assert(name&&own(db().music.cues,name),'Unknown/no active cue');cue=db().music.cues[name];
      // Active sequence freezes its definition; later definition edits affect the next start only.
      if(q.action==='next'){cue=active.sequence;index=active.index+1;}
      assert(index<cue.tracks.length,'End of cue sequence; choose a new cue, no automatic looping');
      cue.tracks.forEach(function(id){obj('jukeboxtrack',id);});target=cue.tracks[index];
    }
    var changes=now.playing.map(function(row){return {id:row.id,changes:{playing:false,softstop:true,loop:false}};});
    if(target){changes=changes.filter(function(r){return r.id!==target;});changes.push({id:target,changes:{playing:true,softstop:false,loop:false,volume:cue.volume}});}
    var plan={action:q.action,cue:target?name:null,index:target?index:null,changes:changes,expect:now.fingerprint};
    if(q.preview===true)return reply(q,{status:'PREVIEW',plan:plan,note:'Stop native playlist in UI first. No playback changed.'});
    assert(q.exclusiveReady===true,'Stop native playlist in UI and confirm exclusiveReady:true');
    assert(q.expect===now.fingerprint,'Stale music state; inspect/preview again');
    fresh(q);
    var tx={request:q.request,at:new Date().toISOString(),status:'STARTED',plan:plan,before:changes.map(function(r){return read(obj('jukeboxtrack',r.id),TRACK);})};
    db().music.receipts.push(tx);if(db().music.receipts.length>12)db().music.receipts.shift();
    try {
      changes.forEach(function(r){obj('jukeboxtrack',r.id).set(r.changes);});
      tx.after=changes.map(function(r){return read(obj('jukeboxtrack',r.id),TRACK);});
      tx.status=changes.every(function(r){return eq(values(obj('jukeboxtrack',r.id),Object.keys(r.changes)),r.changes);})?'VERIFIED_OBJECTS':'MISMATCH';
      if(tx.status==='VERIFIED_OBJECTS')db().music.active=target?{cue:name,index:index,sequence:JSON.parse(JSON.stringify(cue)),startedAt:tx.at,track:target}:null;
      else db().music.active=null;
    }catch(e){tx.status='PARTIAL_FAILURE';tx.error=e.message;db().music.active=null;}
    tx.note='No playhead rollback or audible proof. Read status and UI before retry; next is manual, never a timer.';
    return reply(q,tx);
  }
  function handle(q) {
    assert(q&&typeof q==='object'&&!Array.isArray(q),'Expected JSON object');
    if(q.op==='help')return reply(q,{mode:'READ_LIVE / EDIT_TEST_COPIES / MANUAL_MUSIC',ops:READS.concat(['help','more','batch','music','snapshot','compare','lab','clone','preview','edit','undo','transactions']),lab:db().lab});
    if(q.op==='more'){var entry=receipts.filter(function(r){return r.id===q.receipt;})[0];assert(entry,'Receipt expired/restart; reissue read or use console');return display(entry,q.page);}
    if(READS.indexOf(q.op)>=0)return inspect(q,function(result){reply(q,result);});
    if(q.op==='batch') {
      assert(Array.isArray(q.reads)&&q.reads.length>0&&q.reads.length<=5,'Batch requires 1–5 reads');
      assert(q.reads.every(function(r){return r&&READS.indexOf(r.op)>=0;}),'Batch allows only inspection; no nested batches or mutations');
      var results=[],i=0;
      function next(){if(i===q.reads.length)return reply(q,{results:results});var item=q.reads[i++];try{inspect(item,function(r){results.push({op:item.op,result:r});next();});}catch(e){results.push({op:item.op,result:{error:e.message}});next();}}
      return next();
    }
    if(q.op==='music')return music(q);
    if(q.op==='snapshot') {
      assert(typeof q.label==='string'&&/^[a-zA-Z0-9_-]{1,80}$/.test(q.label),'Invalid snapshot label');
      assert(!own(db().snapshots,q.label),'Snapshot exists; choose a new label');
      assert(Object.keys(db().snapshots).length<20,'Snapshot limit reached; export before maintenance');
      var snap=capture(q); db().snapshots[q.label]={spec:{tokens:q.tokens,attributes:q.attributes||[]},data:snap,at:new Date().toISOString()};
      return reply(q,{label:q.label,saved:snap,note:'Selected fields only; no fiction, knowledge or sheet-worker rollback'});
    }
    if(q.op==='compare') {
      assert(own(db().snapshots,q.label),'Unknown snapshot'); var s=db().snapshots[q.label],now=capture(s.spec),delta=[];
      ['tokens','attributes'].forEach(function(type){now[type].forEach(function(row,i){Object.keys(row).forEach(function(k){if(!eq(row[k],s.data[type][i][k]))delta.push({type:type,id:row.id,field:k,before:s.data[type][i][k],now:row[k]});});});});
      return reply(q,{label:q.label,unchanged:delta.length===0,changes:delta});
    }
    if(q.op==='lab') {
      assert(!db().lab||db().lab===q.page,'Lab already bound');
      var lp=obj('page',q.page); assert(lp.get('name')==='GM Framework Lab','Create a private page named GM Framework Lab first');
      db().lab=lp.id; labPage(); return reply(q,{lab:read(lp,PAGE)});
    }
    if(q.op==='clone') {
      var cloneNames=q.names||RESOURCE; assert(Array.isArray(cloneNames)&&cloneNames.length<=100&&cloneNames.every(function(n){return typeof n==='string';}),'Invalid clone attribute names');
      var lab=labPage(),src=obj('graphic',q.id); assert(typeof src.createCopy==='function','Sandbox v1.5 createCopy required');
      assert(db().testTokens.length<4,'Test token limit reached');
      assert(typeof q.request==='string'&&/^[a-zA-Z0-9_-]{1,80}$/.test(q.request)&&!own(db().used,q.request),'Fresh request label required');
      db().used[q.request]=true;
      var testChar=createObj('character',{name:'GM Framework TEST '+(db().testTokens.length+1),inplayerjournals:'',controlledby:'',archived:true});
      assert(testChar,'Test character creation failed'); db().testCharacters.push(testChar.id);
      var sourceChar=src.get('represents'), resources=[];

      if(sourceChar) attrs(sourceChar).filter(function(a){return cloneNames.indexOf(a.get('name'))>=0;}).forEach(function(a){
        var copy=createObj('attribute',{characterid:testChar.id,name:a.get('name'),current:a.get('current'),max:a.get('max')});
        assert(copy,'Test attribute creation failed'); db().testAttributes.push(copy.id);resources.push(read(copy,['name','current','max']));
      });
      var props={pageid:lab.id,name:'GM Framework TEST '+(db().testTokens.length+1),layer:'gmlayer',left:105,top:105,represents:testChar.id,
        controlledby:'',bar1_link:'',bar2_link:'',bar3_link:'',bar4_link:'',showplayers_name:false,showplayers_bar1:false,showplayers_bar2:false,showplayers_bar3:false,
        has_bright_light_vision:false,has_night_vision:false,emits_bright_light:false,emits_low_light:false,light_radius:'',light_dimradius:'',light_otherplayers:false,light_hassight:false};
      var test=src.createCopy(props); assert(test,'Test token copy failed'); db().testTokens.push(test.id);
      allowed('graphic',test.id);
      return reply(q,{source:src.id,test:read(test,TOKEN),character:testChar.id,attributes:resources,note:'Resource subset copied, no source links. Test character is archived and private.'});
    }
    if(q.op==='preview'||q.op==='edit') return mutation(q);
    if(q.op==='undo') {
      var tx=db().transactions.filter(function(t){return t.request===q.transaction;})[0];assert(tx&&tx.status==='VERIFIED','No verified transaction available');
      var o=allowed(tx.type,tx.id),fields=Object.keys(tx.before);
      assert(eq(values(o,fields),tx.after),'Undo conflict: changed fields differ from transaction readback');
      validate(o,tx.type,tx.before);o.set(tx.before);var result=values(o,fields);tx.status=eq(result,tx.before)?'UNDONE':'UNDO_MISMATCH';
      return reply(q,{transaction:tx.request,status:tx.status,result:result});
    }
    if(q.op==='transactions') return reply(q,{transactions:db().transactions,tests:{tokens:db().testTokens,characters:db().testCharacters,attributes:db().testAttributes}});
    throw new Error('Unknown operation; use help');
  }
  on('ready',function(){
    if(!state[KEY]) state[KEY]={schema:1,lab:null,testTokens:[],testCharacters:[],testAttributes:[],transactions:[],used:{},snapshots:{}};
    if(state[KEY].schema!==1){log('GM Control: incompatible state; disabled');return;}
    if(!db().music)db().music={cues:{},active:null,receipts:[]};
    // Restart preserves definitions/evidence, but never starts music.
    on('chat:message',function(msg){
      if(msg.type!=='api'||!/^!gmctl(?:\s|$)/.test(msg.content)||!playerIsGM(msg.playerid)) return;
      var q={op:'parse'};
      try {assert(msg.content.length<=16000,'Command too long');q=JSON.parse(msg.content.slice(7).trim()||'{"op":"help"}');handle(q);}
      catch(e){reply(q||{op:'parse'},{error:e.message});}
    });
    log('GM Control '+VERSION+' ready; live reads, isolated test edits, manual music cues.');
  });
}());
