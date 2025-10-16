"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import AuroraCanvas from "@/components/AuroraCanvas";

const Logo3D = dynamic(() => import("@/components/Logo3D"), {
  ssr: false,
});

export default function HomePage() {
  const [progress, setProgress] = useState(0);
  const router = useRouter();

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => router.push("/dashboard"), 500);
          return 100;
        }
        return prev + 1;
      });
    }, 30);

    return () => clearInterval(interval);
  }, [router]);

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black">
      <AuroraCanvas />

      <div className="absolute inset-0 flex flex-col items-center justify-center z-10">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8 }}
          className="mb-8"
        >
          <Logo3D />
        </motion.div>

        <motion.h1
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          className="text-6xl font-bold text-white mb-12 tracking-wider"
        >
          ARA RADAR
        </motion.h1>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.8 }}
          className="w-64 space-y-4"
        >
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-400"
              initial={{ width: "0%" }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.1 }}
            />
          </div>
          <div className="text-center">
            <span className="text-5xl font-bold text-cyan-400">{progress}</span>
            <span className="text-2xl text-gray-400 ml-1">%</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
