interface NotificationProps {
  message: string;
  type: "success" | "error";
}

export default function Notification({
  message,
  type,
}: NotificationProps) {
  if (!message) return null;

  return (
    <div
      className={`mb-4 rounded-lg p-4 text-white ${
        type === "success"
          ? "bg-green-600"
          : "bg-red-600"
      }`}
    >
      {message}
    </div>
  );
}