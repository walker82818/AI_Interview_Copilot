import type { Message } from "@/types";
import MessageItem from "./MessageItem";
import InputBox from "./InputBox";
import TypingIndicator from "./TypingIndicator";

interface ChatBoxProps {
  messages: Message[];
  isTyping?: boolean;
  disabled?: boolean;
  onSend: (content: string) => void;
}

export default function ChatBox({
  messages,
  isTyping = false,
  disabled = false,
  onSend,
}: ChatBoxProps) {
  return (
    <div className="flex h-full flex-col rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <p className="text-center text-sm text-zinc-400">
            面试尚未开始，请先选择简历与 JD 后开始对话。
          </p>
        ) : (
          messages.map((msg) => <MessageItem key={msg.id} message={msg} />)
        )}
        {isTyping && <TypingIndicator />}
      </div>
      <InputBox onSend={onSend} disabled={disabled || isTyping} />
    </div>
  );
}
