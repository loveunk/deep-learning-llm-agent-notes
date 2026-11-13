# frozen_string_literal: true

# The normalizer has no gem dependencies. Keep the hook stub small so this can
# also run with plain Ruby, outside the Jekyll bundle used for the site build.
module Jekyll
  module Hooks
    def self.register(*_arguments, &block)
      @callback = block
    end

    def self.callback
      @callback
    end
  end
end

require_relative "../_plugins/inline_math"

cases = [
  ["single formula", 'a $x$ b', 'a $$x$$ b'],
  ["multiple formulas", '$x$ 与 $y$，以及 $2 + 3$', '$$x$$ 与 $$y$$，以及 $$2 + 3$$'],
  ["display math", '$$x + y$$', '$$x + y$$'],
  ["inline code", '`$x$` and $y$', '`$x$` and $$y$$'],
  ["multiple-backtick code", '``$x$ and `code` `` then $y$', '``$x$ and `code` `` then $$y$$'],
  ["fenced code", "```python\n$x$\n```\n$y$\n", "```python\n$x$\n```\n$$y$$\n"],
  ["tilde fence", "~~~text\n$x$\n~~~\n$y$\n", "~~~text\n$x$\n~~~\n$$y$$\n"],
  ["fence with trailing text is not a closing fence", "```text\n```still-code\n$x$\n```\n$y$\n", "```text\n```still-code\n$x$\n```\n$$y$$\n"],
  ["indented code", "    $x$\n\t$y$\n$z$\n", "    $x$\n\t$y$\n$$z$$\n"],
  ["image attributes", '<img src="https://example.test/$x$" title="$y$"> $z$', '<img src="https://example.test/$x$" title="$y$"> $$z$$'],
  ["quoted angle bracket", '<span title="x > $y$">$z$</span>', '<span title="x > $y$">$$z$$</span>'],
  ["ordinary prices", 'Costs $10 per month and $20 per month.', 'Costs $10 per month and $20 per month.'],
  ["adjacent prices", '价格为 $10、$20 或 $30。', '价格为 $10、$20 或 $30。'],
  ["escaped dollars", 'Costs \$10 and \$20; formula $x$.', 'Costs \$10 and \$20; formula $$x$$.'],
  ["escaped dollar inside math", '$x + \$1$', '$$x + \$1$$'],
  ["spaced delimiters are plain text", '$ x $ and $ 5 $', '$ x $ and $ 5 $'],
  ["unmatched delimiter", 'The amount is $20.', 'The amount is $20.']
]

matrix = <<~'TEX'.strip
  $r = \begin{bmatrix} 2 \\ 0.5 \end{bmatrix}$ and $\|r\|$
TEX
expected_matrix = <<~'TEX'.strip
  $$r = \begin{bmatrix} 2 \\ 0.5 \end{bmatrix}$$ and $$\|r\|$$
TEX
cases << ["matrix rows and TeX backslashes", matrix, expected_matrix]

cases.each do |label, source, expected|
  actual = InlineMath.normalize(source)
  raise "#{label}: expected #{expected.inspect}, got #{actual.inspect}" unless actual == expected
  raise "#{label}: normalization must be idempotent" unless InlineMath.normalize(actual) == actual
end

page_type = Struct.new(:data, :extname, :content)
enabled = page_type.new({ "math" => true }, ".md", '$x$')
disabled = page_type.new({ "math" => false }, ".md", '$x$')
html = page_type.new({ "math" => true }, ".html", '$x$')
[enabled, disabled, html].each { |page| Jekyll::Hooks.callback.call(page) }
raise "math pages must be normalized" unless enabled.content == '$$x$$'
raise "non-math pages must remain unchanged" unless disabled.content == '$x$'
raise "non-Markdown pages must remain unchanged" unless html.content == '$x$'

puts "Inline math: #{cases.length} normalization cases and 3 hook cases passed."
