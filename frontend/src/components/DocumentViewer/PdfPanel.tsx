'use client';

import React, { useEffect, useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { X, ZoomIn, ZoomOut, ChevronLeft, ChevronRight } from 'lucide-react';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

interface PdfPanelProps {
  isOpen: boolean;
  onClose: () => void;
  pdfUrl: string;
  title: string;
  initialPage?: number;
}

export default function PdfPanel({ isOpen, onClose, pdfUrl, title, initialPage = 1 }: PdfPanelProps) {
  const [numPages, setNumPages] = useState<number>();
  const [pageNumber, setPageNumber] = useState<number>(initialPage);
  const [scale, setScale] = useState<number>(1.0);
  const [workerReady, setWorkerReady] = useState(false);

  useEffect(() => {
    pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';
    setWorkerReady(true);
  }, []);

  if (!isOpen) return null;

  function onDocumentLoadSuccess({ numPages }: { numPages: number }): void {
    setNumPages(numPages);
    setPageNumber(initialPage > 0 && initialPage <= numPages ? initialPage : 1);
  }

  return (
    <div className="flex flex-col w-full h-full bg-white border-l border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50">
        <h3 className="font-semibold text-gray-800 text-sm truncate pr-4" title={title}>
          {title}
        </h3>
        <button 
          onClick={onClose}
          className="p-1 hover:bg-gray-200 rounded-md transition-colors text-gray-500"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 border-b border-gray-200 bg-white text-sm">
        <div className="flex items-center gap-2">
          <button 
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber(prev => prev - 1)}
            className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-gray-600">
            Trang {pageNumber} / {numPages || '--'}
          </span>
          <button 
            disabled={pageNumber >= (numPages || 1)}
            onClick={() => setPageNumber(prev => prev + 1)}
            className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          <button 
            onClick={() => setScale(prev => Math.max(0.5, prev - 0.1))}
            className="p-1 hover:bg-gray-100 rounded"
            title="Thu nhỏ"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-gray-600 w-12 text-center">
            {Math.round(scale * 100)}%
          </span>
          <button 
            onClick={() => setScale(prev => Math.min(2.5, prev + 0.1))}
            className="p-1 hover:bg-gray-100 rounded"
            title="Phóng to"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* PDF Container */}
      <div className="flex-1 overflow-auto bg-gray-100 flex justify-center p-4">
        {!workerReady ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            Dang khoi tao PDF viewer...
          </div>
        ) : pdfUrl ? (
          <Document
            file={pdfUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            loading={
              <div className="flex items-center justify-center h-full text-gray-500">
                Đang tải tài liệu PDF...
              </div>
            }
            error={
              <div className="flex flex-col items-center justify-center h-full text-red-500 p-4 text-center">
                <p>Không thể tải PDF.</p>
                <p className="text-xs mt-2 text-gray-500 break-all">{pdfUrl}</p>
              </div>
            }
          >
            <div className="shadow-lg">
              <Page 
                pageNumber={pageNumber} 
                scale={scale} 
                renderTextLayer={true}
                renderAnnotationLayer={true}
                className="bg-white"
              />
            </div>
          </Document>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            Không có URL tài liệu.
          </div>
        )}
      </div>
    </div>
  );
}
