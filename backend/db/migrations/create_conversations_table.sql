-- Crear tabla de conversaciones
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    response JSONB NOT NULL,
    source TEXT NOT NULL DEFAULT 'web',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);

-- Agregar políticas de seguridad RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Política para usuarios autenticados: pueden ver sus propias conversaciones
CREATE POLICY "Users can view their own conversations"
    ON conversations
    FOR SELECT
    USING (auth.uid() = user_id);

-- Política para usuarios autenticados: pueden crear sus propias conversaciones
CREATE POLICY "Users can create their own conversations"
    ON conversations
    FOR INSERT
    WITH CHECK (auth.uid() = user_id); 