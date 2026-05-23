import React, { Suspense, useRef, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment, Html, useGLTF, Sky, Water } from '@react-three/drei'
import axios from 'axios'

// API基础URL
const API_BASE = 'http://localhost:8000'

// ============================================================
// 3D模型组件
// ============================================================

function Model({ url, position = [0, 0, 0], name, onClick }) {
  const { scene } = useGLTF(url)
  const [hovered, setHovered] = useState(false)
  
  return (
    <primitive
      object={scene}
      position={position}
      scale={hovered ? 1.02 : 1}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
      onClick={onClick}
    />
  )
}

function Placeholder({ position, name, onClick }) {
  const [hovered, setHovered] = useState(false)
  
  return (
    <mesh
      position={position}
      scale={hovered ? 1.1 : 1}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
      onClick={onClick}
    >
      <boxGeometry args={[10, 15, 10]} />
      <meshStandardMaterial color={hovered ? '#f59e0b' : '#64748b'} />
      <Html position={[0, 10, 0]} center>
        <div style={{
          background: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          whiteSpace: 'nowrap'
        }}>
          {name}
        </div>
      </Html>
    </mesh>
  )
}

// ============================================================
// 景区数据
// ============================================================

const SCENES = [
  {
    id: 'dashuifa',
    name: '大水法',
    description: '西洋楼标志性建筑',
    position: [0, 0, 0],
    year: 1747
  },
  {
    id: 'jiuzhouqingyan',
    name: '九州清晏',
    description: '后湖核心景区',
    position: [50, 0, 0],
    year: 1723
  },
  {
    id: 'fangpuxianjing',
    name: '方壶胜境',
    description: '仙境主题',
    position: [0, 0, 50],
    year: 1750
  },
  {
    id: 'zhengdaguangming',
    name: '正大光明',
    description: '朝政正殿',
    position: [-50, 0, 0],
    year: 1723
  }
]

// ============================================================
// 场景组件
// ============================================================

function YuanmingyuanScene({ onSceneSelect }) {
  return (
    <>
      {/* 环境 */}
      <Sky sunPosition={[100, 50, 100]} />
      <ambientLight intensity={0.5} />
      <directionalLight position={[50, 50, 25]} intensity={1} castShadow />
      
      {/* 水面 */}
      <Water
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.5, 0]}
        args={[500, 500]}
      />
      
      {/* 景区模型/占位符 */}
      {SCENES.map((scene) => (
        <Placeholder
          key={scene.id}
          position={scene.position}
          name={scene.name}
          onClick={() => onSceneSelect(scene)}
        />
      ))}
      
      {/* 相机控制 */}
      <OrbitControls
        makeDefault
        minPolarAngle={0}
        maxPolarAngle={Math.PI / 2}
        minDistance={10}
        maxDistance={200}
      />
    </>
  )
}

// ============================================================
// UI组件
// ============================================================

function SceneInfo({ scene, onClose }) {
  if (!scene) return null
  
  return (
    <div style={{
      position: 'absolute',
      bottom: '20px',
      left: '20px',
      background: 'rgba(0,0,0,0.9)',
      color: 'white',
      padding: '20px',
      borderRadius: '12px',
      maxWidth: '400px',
      zIndex: 100
    }}>
      <button
        onClick={onClose}
        style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          background: 'transparent',
          border: 'none',
          color: 'white',
          fontSize: '20px',
          cursor: 'pointer'
        }}
      >
        ×
      </button>
      <h2 style={{ margin: '0 0 10px' }}>{scene.name}</h2>
      <p style={{ color: '#94a3b8', marginBottom: '10px' }}>
        建于 {scene.year} 年
      </p>
      <p>{scene.description}</p>
      <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
        <button style={{
          background: '#3b82f6',
          color: 'white',
          border: 'none',
          padding: '8px 16px',
          borderRadius: '6px',
          cursor: 'pointer'
        }}>
          查看详情
        </button>
        <button style={{
          background: '#64748b',
          color: 'white',
          border: 'none',
          padding: '8px 16px',
          borderRadius: '6px',
          cursor: 'pointer'
        }}>
          新旧对比
        </button>
      </div>
    </div>
  )
}

function Timeline({ year, onChange }) {
  return (
    <div style={{
      position: 'absolute',
      bottom: '20px',
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'rgba(0,0,0,0.8)',
      padding: '15px 30px',
      borderRadius: '30px',
      display: 'flex',
      alignItems: 'center',
      gap: '15px'
    }}>
      <span style={{ color: 'white', fontSize: '14px' }}>1700</span>
      <input
        type="range"
        min="1700"
        max="1860"
        value={year}
        onChange={(e) => onChange(parseInt(e.target.value))}
        style={{ width: '200px' }}
      />
      <span style={{ color: 'white', fontSize: '14px' }}>1860</span>
      <span style={{
        color: '#f59e0b',
        fontSize: '18px',
        fontWeight: 'bold',
        marginLeft: '10px'
      }}>
        {year}年
      </span>
    </div>
  )
}

function Header() {
  return (
    <header style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      padding: '20px',
      background: 'linear-gradient(to bottom, rgba(0,0,0,0.8), transparent)',
      color: 'white',
      zIndex: 100
    }}>
      <h1 style={{ margin: 0, fontSize: '24px' }}>
        🏛️ 重生·圆明园
      </h1>
      <p style={{ margin: '5px 0 0', color: '#94a3b8', fontSize: '14px' }}>
        AI驱动的数字文化遗产3D重建与沉浸式体验平台
      </p>
    </header>
  )
}

function SceneList({ scenes, onSelect }) {
  return (
    <div style={{
      position: 'absolute',
      top: '100px',
      right: '20px',
      background: 'rgba(0,0,0,0.8)',
      padding: '15px',
      borderRadius: '12px',
      zIndex: 100
    }}>
      <h3 style={{ margin: '0 0 10px', color: 'white', fontSize: '14px' }}>
        重点景区
      </h3>
      {scenes.map((scene) => (
        <div
          key={scene.id}
          onClick={() => onSelect(scene)}
          style={{
            padding: '10px',
            marginBottom: '8px',
            background: 'rgba(255,255,255,0.1)',
            borderRadius: '8px',
            cursor: 'pointer',
            color: 'white',
            fontSize: '14px'
          }}
        >
          <div style={{ fontWeight: 'bold' }}>{scene.name}</div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>
            {scene.description}
          </div>
        </div>
      ))}
    </div>
  )
}

// ============================================================
// 主应用
// ============================================================

export default function App() {
  const [selectedScene, setSelectedScene] = useState(null)
  const [year, setYear] = useState(1860)
  
  return (
    <div style={{ width: '100vw', height: '100vh', background: '#0a0a0a' }}>
      <Header />
      
      <Canvas camera={{ position: [80, 50, 80], fov: 60 }}>
        <Suspense fallback={null}>
          <YuanmingyuanScene onSceneSelect={setSelectedScene} />
        </Suspense>
      </Canvas>
      
      <SceneList scenes={SCENES} onSelect={setSelectedScene} />
      
      <SceneInfo
        scene={selectedScene}
        onClose={() => setSelectedScene(null)}
      />
      
      <Timeline year={year} onChange={setYear} />
    </div>
  )
}
