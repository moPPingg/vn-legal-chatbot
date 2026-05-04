"use client";

import { useRouter } from "next/navigation";

interface LawType {
  value: string;
  label: string;
  desc: string;
}

export default function LawSelector({ lawTypes }: { lawTypes: LawType[] }) {
  const router = useRouter();

  const handleSelect = (lawType: string) => {
    router.push(`/chat?law=${encodeURIComponent(lawType)}`);
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      {lawTypes.map((law) => (
        <div
          key={law.value}
          onClick={() => handleSelect(law.value)}
          className="bg-white border border-gray-200 rounded-xl p-5 cursor-pointer transition hover:shadow-sm hover:border-gray-300"
        >
          <div>
            <p className="font-medium text-gray-900">{law.label}</p>
            <p className="text-sm text-gray-500 mt-1">{law.desc}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
