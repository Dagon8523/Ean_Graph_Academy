export class ApiError extends Error {
  constructor(kind, message, status) {
    super(message);
    this.kind = kind; // 'network' | 'timeout' | 'http' | 'parse'
    this.status = status;
  }
}
