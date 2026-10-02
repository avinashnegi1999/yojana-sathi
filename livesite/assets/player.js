// * The films: our own player bar, as YouTube lays it out. Play, sound and time
// * on the left; CC and full screen on the right; a seek line above. Captions
// * are drawn by the page (the track stays "hidden"), so they sit above the bar
// * and go full screen with it. One CC switch covers both films, and starting
// * one film pauses the other, so two soundtracks never play at once.
(function(){
  const films=[...document.querySelectorAll('.film')];
  const svg=d=>'<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">'+d+'</svg>';
  const IC={
    play:svg('<path d="M8 5.5v13l10.5-6.5z" fill="currentColor"/>'),
    pause:svg('<path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z" fill="currentColor"/>'),
    vol:svg('<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z" fill="currentColor"/><path d="M15 9a4 4 0 0 1 0 6M17.5 6.5a7.5 7.5 0 0 1 0 11" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>'),
    mute:svg('<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z" fill="currentColor"/><path d="M15.5 9.5l5 5M20.5 9.5l-5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>'),
    full:svg('<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'),
    rot:svg('<rect x="7" y="3" width="10" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3 14a9 9 0 0 0 7 7M21 10a9 9 0 0 0-7-7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M8 20.5l2.2.6-.5-2.3M16 3.5l-2.2-.6.5 2.3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'),
    exit:svg('<path d="M9 4v5H4M15 4v5h5M15 20v-5h5M9 20v-5H4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'),
  };
  const fmt=t=>{t=Math.max(0,Math.floor(t||0));return Math.floor(t/60)+':'+String(t%60).padStart(2,'0');};
  const fsEl=()=>document.fullscreenElement||document.webkitFullscreenElement;
  let ccOn=false;const players=[];
  const setCC=on=>{ccOn=on;players.forEach(p=>p.cc());};

  films.forEach(film=>{
    const v=film.querySelector('video'),big=film.querySelector('.play'),track=v.textTracks[0];
    film.insertAdjacentHTML('beforeend',
      '<div class="cap"></div><div class="bar">'+
      '<div class="seek" role="slider" tabindex="0" aria-label="Seek" aria-valuemin="0" aria-valuenow="0"><i class="buf"></i><i class="done"></i><b></b></div>'+
      '<div class="row"><button type="button" class="b-play" aria-label="Play">'+IC.play+'</button>'+
      '<button type="button" class="b-vol" aria-label="Mute">'+IC.vol+'</button>'+
      '<span class="time">0:00 / 0:00</span><span class="gap"></span>'+
      '<button type="button" class="b-cc" aria-pressed="false" aria-label="Captions" title="Captions (c)"><span>CC</span></button>'+
      '<button type="button" class="b-rot" aria-label="Rotate" title="Rotate">'+IC.rot+'</button>'+
      '<button type="button" class="b-full" aria-label="Full screen" title="Full screen (f)">'+IC.full+'</button></div></div>');
    const $=q=>film.querySelector(q);
    const cap=$('.cap'),seek=$('.seek'),done=$('.done'),buf=$('.buf'),knob=$('.seek b'),time=$('.time');
    const bPlay=$('.b-play'),bVol=$('.b-vol'),bCC=$('.b-cc'),bFull=$('.b-full');
    if(track)track.mode='hidden';

    // the bar shows while paused, and for a moment after any movement
    let idle;
    const wake=()=>{film.classList.add('show');clearTimeout(idle);
      idle=setTimeout(()=>{if(!v.paused&&!seek.classList.contains('drag'))film.classList.remove('show');},2500);};
    film.addEventListener('pointermove',wake);
    film.addEventListener('focusin',wake);

    const toggle=()=>{if(v.paused||v.ended)v.play();else v.pause();};
    big.addEventListener('click',toggle);
    bPlay.addEventListener('click',toggle);
    v.addEventListener('click',e=>{
      // * on a phone, the first tap brings the bar back; the next one pauses
      if(e.pointerType==='touch'&&!film.classList.contains('show')&&!v.paused){wake();return;}
      toggle();});
    v.addEventListener('dblclick',()=>bFull.click());
    v.addEventListener('play',()=>{
      film.classList.add('playing','started');bPlay.innerHTML=IC.pause;bPlay.setAttribute('aria-label','Pause');wake();
      films.forEach(other=>{if(other!==film)other.querySelector('video').pause();});
    });
    const stopped=()=>{film.classList.remove('playing');film.classList.add('show');clearTimeout(idle);
      bPlay.innerHTML=IC.play;bPlay.setAttribute('aria-label','Play');};
    v.addEventListener('pause',stopped);
    v.addEventListener('ended',stopped);

    const draw=()=>{const d=v.duration||0,f=d?v.currentTime/d:0;
      done.style.width=knob.style.left=(f*100)+'%';
      time.textContent=fmt(v.currentTime)+' / '+fmt(d);
      seek.setAttribute('aria-valuemax',Math.round(d));seek.setAttribute('aria-valuenow',Math.round(v.currentTime));
      seek.setAttribute('aria-valuetext',fmt(v.currentTime)+' of '+fmt(d));};
    v.addEventListener('timeupdate',draw);
    v.addEventListener('loadedmetadata',draw);
    v.addEventListener('progress',()=>{const d=v.duration,b=v.buffered;if(d&&b.length)buf.style.width=(b.end(b.length-1)/d*100)+'%';});

    const at=e=>{const r=seek.getBoundingClientRect();return Math.min(1,Math.max(0,(e.clientX-r.left)/r.width));};
    seek.addEventListener('pointerdown',e=>{if(!v.duration)return;seek.setPointerCapture(e.pointerId);seek.classList.add('drag');v.currentTime=at(e)*v.duration;draw();});
    seek.addEventListener('pointermove',e=>{if(seek.classList.contains('drag')){v.currentTime=at(e)*v.duration;draw();}});
    const release=()=>{seek.classList.remove('drag');wake();};
    seek.addEventListener('pointerup',release);
    seek.addEventListener('pointercancel',release);

    bVol.addEventListener('click',()=>{v.muted=!v.muted;});
    v.addEventListener('volumechange',()=>{bVol.innerHTML=v.muted?IC.mute:IC.vol;bVol.setAttribute('aria-label',v.muted?'Unmute':'Mute');});

    const show=()=>{const c=track&&track.activeCues&&track.activeCues[0];cap.textContent=ccOn&&c?c.text:'';};
    if(track)track.addEventListener('cuechange',show);
    bCC.addEventListener('click',()=>setCC(!ccOn));
    players.push({cc(){bCC.setAttribute('aria-pressed',ccOn);show();}});

    bFull.addEventListener('click',()=>{
      if(fsEl()){(document.exitFullscreen||document.webkitExitFullscreen).call(document);return;}
      // turn sideways the moment full screen is granted, still inside the tap
      if(film.requestFullscreen)film.requestFullscreen({navigationUI:'hide'}).then(()=>turn('landscape')).catch(()=>{});
      else if(film.webkitRequestFullscreen)film.webkitRequestFullscreen();
      else if(v.webkitEnterFullscreen)v.webkitEnterFullscreen(); // iPhone: the system player, with its own captions menu
    });
    // * On a phone, full screen turns the film sideways, as YouTube does; the
    // * rotate button (full screen only) turns it back upright or sideways again.
    // * Browsers allow this only in full screen, and iPhones not at all: there
    // * the system player turns with the phone instead.
    const phone=matchMedia('(pointer:coarse)').matches;
    const so=screen.orientation;
    const canTurn=phone&&so&&typeof so.lock==='function';
    const turn=to=>{if(canTurn)so.lock(to).catch(()=>{});};
    const bRot=$('.b-rot');
    bRot.addEventListener('click',()=>turn(so.type.startsWith('landscape')?'portrait':'landscape'));
    // * React only when this film enters or leaves full screen: the project
    // * page has two films, and the other one must not release the rotation.
    let full=false;
    const fsChange=()=>{const on=fsEl()===film;if(on===full)return;full=on;bFull.innerHTML=on?IC.exit:IC.full;bFull.setAttribute('aria-label',on?'Exit full screen':'Full screen');
      film.classList.toggle('can-turn',on&&canTurn);
      if(on)turn('landscape');else if(canTurn&&so.unlock)so.unlock();};
    document.addEventListener('fullscreenchange',fsChange);
    document.addEventListener('webkitfullscreenchange',fsChange);

    film.addEventListener('keydown',e=>{
      if(e.target.closest('button')&&(e.key===' '||e.key==='Enter'))return;
      const k=e.key.toLowerCase();
      if(k===' '||k==='k'){e.preventDefault();toggle();}
      else if(k==='c'){setCC(!ccOn);wake();}
      else if(k==='f')bFull.click();
      else if(k==='m')v.muted=!v.muted;
      else if(k==='arrowright'||k==='arrowleft'){e.preventDefault();v.currentTime=Math.max(0,v.currentTime+(k==='arrowright'?5:-5));wake();}
    });
  });
})();
