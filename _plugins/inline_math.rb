# frozen_string_literal: true

# GitHub accepts $inline math$, while kramdown expects $$inline math$$.
# Normalize only explicitly opted-in math pages before Markdown conversion so
# backslashes and matrix rows survive. The repository sources remain unchanged.
module InlineMath
  def self.normalize(content)
    fence = nil
    content.lines.map do |line|
      marker = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/)
      if fence
        fence = nil if marker && marker[1][0] == fence[0] && marker[1].length >= fence.length && marker[2].strip.empty?
        next line
      elsif marker
        fence = marker[1]
        next line
      end

      next line if line.start_with?("    ", "\t")

      # Leave inline code and HTML attributes (including old formula URLs) alone.
      # Tight delimiters and a nonnumeric character after the closing delimiter
      # keep ordinary prices such as "$10 and $20" out of the math parser.
      line.gsub(/(`+)(.*?)\1|<(?:"[^"]*"|'[^']*'|[^'">])*>|(?<![\\$])\$(?![\s$])((?:\\[^\n]|[^\\$\n])+?)(?<![\s\\])\$(?![$\d])/) do |match|
        formula = Regexp.last_match(3)
        formula ? "$$#{formula}$$" : match
      end
    end.join
  end
end

Jekyll::Hooks.register :pages, :pre_render do |page|
  next unless page.data["math"] == true && page.extname == ".md"

  page.content = InlineMath.normalize(page.content)
end
