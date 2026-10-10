(() => {
  const $ = id => document.getElementById(id);
  const video = $('video'), canvas = $('overlay'), ctx = canvas.getContext('2d');
  let stream = null, mesh = null, camera = null, running = false, lowSince = null;
  let locationCoords = null, lastAlertAt = 0, eventCounter = 0;
  const EAR_THRESHOLD = 0.21; // Initial heuristic only; test/tune before real-world use.
  const CLOSED_SECONDS = 10.0;
  const ALERT_COOLDOWN_MS = 60000;
  const LEFT = [33,160,158,133,153,144], RIGHT = [362,385,387,263,373,380];
  const dist = (a,b) => Math.hypot(a.x-b.x,a.y-b.y);
  function ear(lm, ids) { const p=ids.map(i=>lm[i]); return (dist(p[1],p[5])+dist(p[2],p[4]))/(2*dist(p[0],p[3])||1); }
  function state(label,hint,kind='') { $('state').textContent=label; $('hint').textContent=hint; $('badge').textContent=running?'Monitoring':'Camera off'; $('badge').className='badge '+(kind || (running?'live':'')); if(kind==='alert') $('badge').textContent='Check alertness'; }
  function log(message) { const list=$('events'); const empty=list.querySelector('.empty'); if(empty) empty.remove(); const li=document.createElement('li'); li.textContent=new Date().toLocaleTimeString()+' · '+message; list.prepend(li); while(list.children.length>8) list.lastElementChild.remove(); }
  function beep() { try { const AC=window.AudioContext||window.webkitAudioContext; const ac=new AC(); [0,.28,.56].forEach(t=>{const o=ac.createOscillator(),g=ac.createGain();o.frequency.value=880;o.type='sawtooth';g.gain.setValueAtTime(.0001,ac.currentTime+t);g.gain.exponentialRampToValueAtTime(.16,ac.currentTime+t+.02);g.gain.exponentialRampToValueAtTime(.0001,ac.currentTime+t+.18);o.connect(g);g.connect(ac.destination);o.start(ac.currentTime+t);o.stop(ac.currentTime+t+.2);});}catch(e){console.warn(e);} }
  function draw(lm) { canvas.width=video.videoWidth||640; canvas.height=video.videoHeight||480; ctx.clearRect(0,0,canvas.width,canvas.height); [LEFT,RIGHT].forEach(ids=>{ctx.beginPath();ids.forEach((id,i)=>{const p=lm[id];if(!i)ctx.moveTo(p.x*canvas.width,p.y*canvas.height);else ctx.lineTo(p.x*canvas.width,p.y*canvas.height);});ctx.closePath();ctx.strokeStyle='#9fb4ff';ctx.lineWidth=2;ctx.stroke();}); }
  async function sendAlert() {
    if(!$('consent').checked){log('Local warning only; emergency sharing is not enabled');return;}
    const contact=$('contact').value.trim(); if(!contact){log('Alert not sent: add an emergency contact');return;}
    const maps=locationCoords?`https://www.google.com/maps?q=${locationCoords.latitude},${locationCoords.longitude}`:'';
    try { const r=await fetch('/api/alert',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({contact,consent:true,maps_url:maps,event_id:`${Date.now()}-${++eventCounter}`,event_type:'possible_drowsiness'})}); const data=await r.json(); log(data.message||'Alert request finished'); }
    catch(e){log('Alert service unavailable; local warning only');}
  }
  async function results(out) {
    if(!running)return; const faces=out.multiFaceLandmarks;
    if(!faces||!faces.length){lowSince=null;$('ear').textContent='—';$('duration').textContent='0.0s';ctx.clearRect(0,0,canvas.width,canvas.height);state('Face not detected','Improve lighting and face the camera');return;}
    const lm=faces[0];draw(lm);const value=(ear(lm,LEFT)+ear(lm,RIGHT))/2;$('ear').textContent=value.toFixed(3);const now=performance.now();
    if(value<EAR_THRESHOLD){if(lowSince===null)lowSince=now;const secs=(now-lowSince)/1000;$('duration').textContent=secs.toFixed(1)+'s';if(secs>=CLOSED_SECONDS){state('Possible drowsiness','Prolonged eye-closure estimate — take a safe break','alert');if(now-lastAlertAt>ALERT_COOLDOWN_MS){lastAlertAt=now;log('Possible prolonged eye closure detected');beep();await sendAlert();}}else state('Eyes possibly closing','Checking consecutive frames');}
    else{lowSince=null;$('duration').textContent='0.0s';state('Monitoring','No prolonged closure detected');}
  }
  async function start(){
    if(running)return;
    if(!window.isSecureContext&&location.hostname!=='localhost'&&location.hostname!=='127.0.0.1'){$('cameraMessage').textContent='Camera access requires HTTPS on the deployed site.';return;}
    if(!window.FaceMesh||!window.Camera){$('cameraMessage').textContent='Vision libraries did not load. Check your internet connection and refresh.';return;}
    try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});video.srcObject=stream;video.style.display='block';$('placeholder').style.display='none';await video.play();mesh=new FaceMesh({locateFile:f=>`https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}`});mesh.setOptions({maxNumFaces:1,refineLandmarks:true,minDetectionConfidence:.55,minTrackingConfidence:.55});mesh.onResults(results);camera=new Camera(video,{onFrame:async()=>{if(running&&mesh)await mesh.send({image:video});},width:640,height:480});running=true;await camera.start();$('start').disabled=true;$('stop').disabled=false;$('cameraMessage').textContent='Monitoring is active. Keep your face visible and the device steady.';state('Starting','Waiting for face detection');log('Monitoring started');}
    catch(e){stop();$('cameraMessage').textContent='Camera could not start. Check browser permission and whether another app is using it.';}
  }
  function stop(){running=false;lowSince=null;try{if(camera&&camera.stop)camera.stop();}catch(e){}try{if(mesh&&mesh.close)mesh.close();}catch(e){}if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;camera=null;mesh=null;video.srcObject=null;video.style.display='none';$('placeholder').style.display='flex';ctx.clearRect(0,0,canvas.width,canvas.height);$('start').disabled=false;$('stop').disabled=true;$('duration').textContent='0.0s';$('ear').textContent='—';state('Not monitoring','Start when ready');$('cameraMessage').textContent='Camera stopped. This app does not upload camera frames.';}
  $('start').addEventListener('click',start);$('stop').addEventListener('click',stop);$('test').addEventListener('click',()=>{beep();log('Sound test played');});
  $('location').addEventListener('click',()=>{if(!navigator.geolocation){$('locationStatus').textContent='Geolocation is not supported by this browser.';return;}$('locationStatus').textContent='Requesting permission…';navigator.geolocation.getCurrentPosition(p=>{locationCoords={latitude:p.coords.latitude,longitude:p.coords.longitude};$('locationStatus').textContent='Permission granted for this session. Location is included only in an opted-in alert.';log('Location permission granted');},()=>{$('locationStatus').textContent='Location not shared. You can continue without it.';locationCoords=null;},{timeout:10000,maximumAge:60000});});
  $('save').addEventListener('click',()=>{const c=$('contact').value.trim();if(c&&!/^\+[1-9]\d{7,14}$/.test(c)){$('settingsMessage').textContent='Use international phone format, e.g. +91XXXXXXXXXX.';return;}try{localStorage.setItem('drowsiness_contact',c);}catch(e){}$('settingsMessage').textContent='Contact saved on this device only.';});
  $('clear').addEventListener('click',()=>$('events').innerHTML='<li class="empty">No events yet.</li>');try{const c=localStorage.getItem('drowsiness_contact');if(c)$('contact').value=c;}catch(e){}window.addEventListener('beforeunload',stop);
})();
