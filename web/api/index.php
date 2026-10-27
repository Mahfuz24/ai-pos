<?php
declare(strict_types=1);
// AI-POS cPanel-compatible API placeholder. No authentication or role execution enabled.
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, max-age=0');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: no-referrer');
http_response_code(503);
echo json_encode([
    'service' => 'ai-pos',
    'status' => 'not_ready',
    'authentication' => 'disabled',
    'orchestration' => 'disabled',
    'release' => 'blocked',
], JSON_UNESCAPED_SLASHES);
