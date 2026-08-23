import { useEffect, useRef } from 'react'
import * as THREE from 'three'

// Animated aurora backdrop rendered with three.js (WebGL).
// Mirrors ThreeUI's immersive shader aesthetic without external asset deps.
const frag = `
precision highp float;
uniform float u_time;
uniform vec2 u_res;
varying vec2 v_uv;

float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p){
  vec2 i=floor(p), f=fract(p);
  float a=hash(i), b=hash(i+vec2(1.,0.)), c=hash(i+vec2(0.,1.)), d=hash(i+vec2(1.,1.));
  vec2 u=f*f*(3.-2.*f);
  return mix(a,b,u.x)+(c-a)*u.y*(1.-u.x)+(d-b)*u.x*u.y;
}
float fbm(vec2 p){
  float v=0., a=0.5;
  for(int i=0;i<5;i++){ v+=a*noise(p); p*=2.02; a*=0.5; }
  return v;
}
void main(){
  vec2 uv=v_uv;
  vec2 p=uv*3.0;
  float t=u_time*0.05;
  float n=fbm(p+vec2(t, t*0.7));
  float n2=fbm(p*1.4-vec2(t*0.6, t));
  vec3 indigo=vec3(0.39,0.40,0.95);
  vec3 violet=vec3(0.66,0.33,0.97);
  vec3 cyan=vec3(0.13,0.83,0.93);
  vec3 col=mix(indigo, violet, smoothstep(0.2,0.8,n));
  col=mix(col, cyan, smoothstep(0.4,0.9,n2)*0.5);
  float glow=smoothstep(0.6,1.0,n)*0.5;
  col+=glow*0.25;
  // vignette
  float d=distance(uv, vec2(0.5));
  col*= 1.0 - d*0.7;
  gl_FragColor=vec4(col*0.9, 1.0);
}
`

const vert = `
varying vec2 v_uv;
void main(){ v_uv=uv; gl_Position=vec4(position,1.0); }
`

export default function AuroraBackground() {
  const ref = useRef(null)
  useEffect(() => {
    const mount = ref.current
    const w = mount.clientWidth
    const h = mount.clientHeight
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
    renderer.setSize(w, h)
    mount.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    const camera = new THREE.Camera()
    const geo = new THREE.PlaneGeometry(2, 2)
    const uniforms = { u_time: { value: 0 }, u_res: { value: new THREE.Vector2(w, h) } }
    const mat = new THREE.ShaderMaterial({ vertexShader: vert, fragmentShader: frag, uniforms })
    const mesh = new THREE.Mesh(geo, mat)
    scene.add(mesh)

    let raf
    const clock = new THREE.Clock()
    const animate = () => {
      uniforms.u_time.value = clock.getElapsedTime()
      renderer.render(scene, camera)
      raf = requestAnimationFrame(animate)
    }
    animate()

    const onResize = () => {
      const nw = mount.clientWidth, nh = mount.clientHeight
      renderer.setSize(nw, nh)
      uniforms.u_res.value.set(nw, nh)
    }
    window.addEventListener('resize', onResize)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', onResize)
      geo.dispose(); mat.dispose(); renderer.dispose()
      if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement)
    }
  }, [])
  return (
    <div
      ref={ref}
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        filter: 'blur(12px) saturate(1.1)',
        opacity: 0.55,
      }}
    />
  )
}
