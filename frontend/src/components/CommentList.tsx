import type { Comment } from '../api/types';
import { relativeTime } from '../lib/format';
import { Avatar } from './ui';

export function CommentList({ comments }: { comments: Comment[] }) {
  if (comments.length === 0) {
    return (
      <div className="empty">
        <p className="empty__title">No comments yet</p>
        <p className="empty__text">Write the first one below — decisions live better in the thread than in a chat app.</p>
      </div>
    );
  }

  return (
    <div>
      {comments.map((comment) => (
        <article className="comment" key={comment.id}>
          <div className="comment__head">
            <Avatar user={comment.author} size="sm" />
            <span className="comment__author">{comment.author.name}</span>
            <time className="comment__time" dateTime={comment.created_at}>
              {relativeTime(comment.created_at)}
            </time>
          </div>
          <p className="comment__body">{comment.body}</p>
        </article>
      ))}
    </div>
  );
}
