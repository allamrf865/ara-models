"use client";

import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Text3D, Center } from "@react-three/drei";
import * as THREE from "three";

function RotatingText() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.3;
      meshRef.current.rotation.x = Math.cos(state.clock.elapsedTime * 0.3) * 0.1;
    }
  });

  return (
    <Center>
      <mesh ref={meshRef}>
        <boxGeometry args={[2, 2, 2]} />
        <meshStandardMaterial
          color="#3b82f6"
          emissive="#1e40af"
          emissiveIntensity={0.5}
          metalness={0.8}
          roughness={0.2}
        />
      </mesh>
    </Center>
  );
}

export default function Logo3D() {
  return (
    <div className="w-48 h-48">
      <Canvas camera={{ position: [0, 0, 5], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -10, -10]} intensity={0.5} />
        <RotatingText />
      </Canvas>
    </div>
  );
}
