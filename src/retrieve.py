# cert-aai-2026-06-0061  Sarath Chandra
#
# - Finds the earlier messages in a conversation that could answer a reply
# - Looks only inside the same conversation, so a citation is always a message that really came first

from store import Message, Store


def earlier(store: Store, message: Message) -> tuple[Message, ...]:
    thread = store.thread(message.thread_id)
    return thread[:thread.index(message)]


def offered(store: Store, message: Message) -> set[str]:
    return {found.id for found in earlier(store, message)}
