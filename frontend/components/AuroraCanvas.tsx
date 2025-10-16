"use client";

import { useEffect, useRef } from "react";

const AuroraCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const stars: Array<{ x: number; y: number; size: number; speed: number }> = [];
    for (let i = 0; i < 200; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2,
        speed: Math.random() * 0.5 + 0.1,
      });
    }

    let time = 0;
    const animate = () => {
      ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
      gradient.addColorStop(0, `rgba(0, ${100 + Math.sin(time * 0.001) * 50}, 255, 0.1)`);
      gradient.addColorStop(0.5, `rgba(100, ${50 + Math.cos(time * 0.002) * 50}, 255, 0.08)`);
      gradient.addColorStop(1, `rgba(0, 255, ${200 + Math.sin(time * 0.0015) * 55}, 0.06)`);

      for (let i = 0; i < 3; i++) {
        const y = canvas.height * 0.3 + Math.sin(time * 0.001 + i) * 100;
        const x = (time * 0.5 + i * canvas.width / 3) % canvas.width;

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.ellipse(x, y, 200, 100, Math.sin(time * 0.001) * 0.5, 0, Math.PI * 2);
        ctx.fill();
      }

      stars.forEach((star) => {
        star.y += star.speed;
        if (star.y > canvas.height) {
          star.y = 0;
          star.x = Math.random() * canvas.width;
        }

        ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
        ctx.fill();
      });

      time++;
      requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full"
    />
  );
};

export default AuroraCanvas;
