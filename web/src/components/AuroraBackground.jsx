import { useEffect, useRef } from 'react'
import * as THREE from 'three'

// Subtle three.js "data field": drifting points, like a ranked constellation.
// Technical texture rather than a decorative gradient blob.
const COUNT = 520

export default function AuroraBackground() {
  const ref = useRef(null)
  useEffect(() => {
    const mount = ref.current
    if (!mount) return
    let renderer, geo, mat, raf
    try {
      const w = mount.clientWidth || window.innerWidth
      const h = mount.clientHeight || window.innerHeight
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
      renderer.setSize(w, h)
      mount.appendChild(renderer.domElement)

      const scene = new THREE.Scene()
      const camera = new THREE.PerspectiveCamera(60, w / h, 0.1, 100)
      camera.position.z = 14

      const positions = new Float32Array(COUNT * 3)
      const speeds = new Float32Array(COUNT)
      for (let i = 0; i < COUNT; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 26
        positions[i * 3 + 1] = (Math.random() - 0.5) * 16
        positions[i * 3 + 2] = (Math.random() - 0.5) * 10
        speeds[i] = 0.2 + Math.random() * 0.6
      }
      geo = new THREE.BufferGeometry()
      geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
      mat = new THREE.PointsMaterial({
        color: 0x16161a,
        size: 0.05,
        transparent: true,
        opacity: 0.35,
        sizeAttenuation: true,
      })
      const points = new THREE.Points(geo, mat)
      scene.add(points)

      const mouse = { x: 0, y: 0 }
      const onMove = (e) => {
        mouse.x = (e.clientX / window.innerWidth - 0.5) * 2
        mouse.y = (e.clientY / window.innerHeight - 0.5) * 2
      }
      window.addEventListener('mousemove', onMove)

      const pos = geo.attributes.position
      const clock = new THREE.Clock()
      const animate = () => {
        const t = clock.getElapsedTime()
        for (let i = 0; i < COUNT; i++) {
          let y = pos.array[i * 3 + 1] + speeds[i] * 0.01
          if (y > 8) y = -8
          pos.array[i * 3 + 1] = y
          pos.array[i * 3] += Math.sin(t * 0.2 + i) * 0.002
        }
        pos.needsUpdate = true
        points.rotation.y = t * 0.02 + mouse.x * 0.15
        points.rotation.x = mouse.y * 0.08
        renderer.render(scene, camera)
        raf = requestAnimationFrame(animate)
      }
      animate()

      const onResize = () => {
        const nw = mount.clientWidth || window.innerWidth
        const nh = mount.clientHeight || window.innerHeight
        renderer.setSize(nw, nh)
        camera.aspect = nw / nh
        camera.updateProjectionMatrix()
      }
      window.addEventListener('resize', onResize)
      return () => {
        cancelAnimationFrame(raf)
        window.removeEventListener('mousemove', onMove)
        window.removeEventListener('resize', onResize)
        geo.dispose(); mat.dispose(); renderer.dispose()
        if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement)
      }
    } catch (err) {
      console.error('AuroraBackground disabled:', err)
      if (renderer) renderer.dispose()
      if (geo) geo.dispose()
      if (mat) mat.dispose()
    }
  }, [])
  return (
    <div
      ref={ref}
      aria-hidden="true"
      style={{ position: 'fixed', inset: 0, zIndex: 0, opacity: 0.5, pointerEvents: 'none' }}
    />
  )
}
